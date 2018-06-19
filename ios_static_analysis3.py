import os
import sys
import getpass
import time
import paramiko
from collections import OrderedDict

class bcolors:
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'

def open_ssh_connection():
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	print '\n########### Login ###########'
	#username = raw_input('  username: ')
	#hostname = raw_input('  hostname: ')
	#password = getpass.getpass('  password: ')
	username = 'root'
	hostname = '10.76.20.139'
	password = 'tetas'
	print '  Connecting...'
	ssh.connect(hostname, 22, username, password)
	print '###############################\n'
	
	return ssh

def choose_application(ssh):
	applications = []
	s = send_command(ssh,'ipainstaller -l').split('\n')[1:-1]

	print '\n########### Installed Applications ###########'
	
	for i,line in enumerate(s): # the first one is the command and the second one a null 
		applications.append(line)
		print "  " + str(i) + ". " + applications[i]
	
	print '################################################\n'

	num = int(input('Select the application: '))
	while num < 0 or num >= len(applications):
		num = int(input('Select the application: '))

	s = send_command(ssh,'ipainstaller -i ' + applications[num]).split('\n')[:-1]
	dictionary = {}
	for line in s:
		name = line.split(':')[0]
		content = line.split(':')[1].strip()
		dictionary[name] = content

	return dictionary

'''
def dynamic_path(ssh, app):
	ssh.sendline ('cycript -p ' + app['pid']) 
	ssh.sendline ('[[[NSFileManager defaultManager] URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask] lastObject];') 
	ssh.prompt()

	app['dynamic_path'] = ssh.before.split('"')[1].split("file://")[1].split("Documents/")[0]

	ssh.sendline ('?exit') 
	ssh.prompt()
'''

def send_command(ssh,c):
	stdin, stdout, stderr = ssh.exec_command(c)
	return stdout.read()

def check_pie(*argv):
	ssh = argv[0]
	app = argv[1]

	s = send_command(ssh,'otool -hv ' + os.path.join(app['Application'],app['Display Name']))

	if "PIE" in s:
		app['pie'] = 0
	else:
		app['pie'] = 1
	
	if "MH_MAGIC_64" in s:
		app['cpu'] = "ARM 64 bits"
	else:
		app['cpu'] = "ARM 32 bits"

def check_stack(*argv):
	ssh = argv[0]
	app = argv[1]

	s = send_command(ssh, 'otool -I -v ' + os.path.join(app['Application'],app['Display Name']))

	if "stack_chk_guard" in s and "stack_chk_fail" in s:
		app['stack'] = 0
	else:
		app['stack'] = 1


def check_arc(*argv):
	ssh = argv[0]
	app = argv[1]

	s = send_command(ssh, 'otool -I -v ' + os.path.join(app['Application'],app['Display Name']) + ' | grep _objc_')
	
	objc = [
		'_objc_retain',
		'_objc_release',
		'_objc_storeStrong',
		'_objc_releaseReturnValue',
		'_objc_autoreleaseReturnValue',
		'_objc_retainAutoreleaseReturnValue',
	]
	if not all(x in s for x in objc):
		app['arc'] = 0
	else:
		app['arc'] = 1


def get_files_by_extension(*argv):
	ssh = argv[0]
	app = argv[1]

	exts = [
		"plist",
		"sql",
		"db",
		"xml",
	]
	for ext in exts:
		s = send_command(ssh,'find ' + app['Bundle'] + ' -iname "*.' + ext + '*"')
		
		# Es descarta la primera perque es la comanda i la ultima es un salt de linia buit
		files = s.split('\n')[1:-1] 
		app[ext] = files

def convert_plist(*argv):
	ssh = argv[0]
	app = argv[1]

	for file in app['plist']:
		send_command(ssh,'plutil -convert xml1 -i ' + file)


def print_menu(options):
	print '\n########### MENU ###########'

	for key in options:
		print "\n"+str(key)
		for i in sorted(options[key]):
			print '  {}. {}'.format(i,options[key][i][1])
	
	print '\n  0. Exit'
	print '#############################\n'

def show_app_info(*argv):
	ssh = argv[0]
	app = argv[1]

	print '\n########### APPLICATION INFO ###########'
	print 'Name: ' + str(app['Name'])
	print 'Short version: ' + str(app['Short Version'])
	print 'Version: ' + str(app['Version'])
	print 'Binary name: ' + str(app['Display Name'])
	print 'Identifier: ' + str(app['Identifier'])
	print 'Bundle: ' + str(app['Bundle'])
	print 'Data: ' + str(app['Data'])
	print '##########################################\n'

def set_key_words(*argv):
	ssh = argv[0]
	app = argv[1]
	keywords = argv[2]

	keywords = raw_input('Enter key words: ')
	return keywords.split(' ')
		

def check_keyboard(*argv):
	ssh = argv[0]
	app = argv[1]
	keywords = argv[2]

	if keywords:
		app['keyboard'] = []
		for key in keywords:
			r1 = send_command(ssh,'grep -rnw "/var/mobile/Library/Keyboard/" -e "'+key+'"')
			r2 = send_command(ssh,'grep -rnw "'+app['Data']+'/Library/Keyboard/" -e "'+key+'"')
			if r1 or r2:
				app['keyboard'].append(key)


def check_pasteboard_leakage(*argv):
	ssh = argv[0]
	app = argv[1]
	keywords = argv[2]

	if keywords:
		app['pasteboard'] = []
		for key in keywords:
			r1 = send_command(ssh,'grep -rnw "/private/var/mobile/Library/Caches/com.apple.UIKit.pboard" -e "'+key+'"')
			if r1:
				app['pasteboard'].append(key)


def check_nsuserdefaults(*argv):
	ssh = argv[0]
	app = argv[1]
	keywords = argv[2]

	if keywords:
		app['nsuserdefaults'] = []
		for key in keywords:
			r1 = send_command(ssh,'grep -rnw "'+app['Data']+'/Library/Preferences/" -e "'+key+'"')
			if r1:
				app['nsuserdefaults'].append(key)


def check_cache(*argv):
	ssh = argv[0]
	app = argv[1]
	keywords = argv[2]

	if keywords:
		app['cache'] = []
		for key in keywords:
			r1 = send_command(ssh,'grep -rnw "'+app['Data']+'/Library/Caches/"'+app['Identifier']+' -e "'+key+'"')
			if r1:
				app['cache'].append(key)


def basic_checks(*argv):
	ssh = argv[0]
	app = argv[1]
	options = argv[3]

	for opt in options['Basic checks']:
		keywords = options['Basic checks'][opt][0](ssh,app)
	

def login_required(*argv):
	ssh = argv[0]
	app = argv[1]
	keywords = argv[2]
	options = argv[3]

	for opt in options['Login required']:
		keywords = options['Login required'][opt][0](ssh,app,keywords)

def show_vulnerabilities(*argv):
	app = argv[1]

	print '\n########### DETECTED VULNERABILITIES ###########'

	print '##################################################\n'

def main(args):
	OPTIONS = OrderedDict()

	OPTIONS['Tests'] = {
		1: (basic_checks,'Run all the basic checks'),
		2: (login_required,'Run all the login required checks')
	}
	OPTIONS['Basic checks'] = {
		3: (check_pie,'Check Position Independent Executable (PIE)'),
		4: (check_stack,'Check Stack Smashing Protections'),
		5: (check_arc,'Automatic Reference Counting (ARC)'),
		6: (get_files_by_extension,'Get sensible files'),
	}
	OPTIONS['Login required'] = {
		7: (check_keyboard,'Check keyboard leakage'),
		8: (check_pasteboard_leakage,'Check pasteboard leakage'),
		9: (check_nsuserdefaults,'Check NSUserDefaults leakage'),
		10: (check_cache,'Check cache leakage'),
	}
	OPTIONS['Other'] = {
		11: (convert_plist,'Convert binary plist to XML'),
	}
	OPTIONS['Configuration'] = {
		12: (set_key_words,'Set key words'),
	}
	OPTIONS['Results'] = {
		13: (show_app_info,'Show app basic information'),
		14: (show_vulnerabilities,'Show detected vulnerabilities'),
	}

	keywords = []

	ssh = open_ssh_connection()
	app = choose_application(ssh)
	
	option = 1
	while int(option):
		print_menu(OPTIONS)
		option = int(raw_input('Select an option: '))

		for key in OPTIONS:
			if option in OPTIONS[key]:
				if option == 12: # set keywords
					keywords = OPTIONS[key][option][0](ssh,app,keywords,OPTIONS)
				else:
					OPTIONS[key][option][0](ssh,app,keywords,OPTIONS)
		
		print app

	ssh.close()


if __name__ == '__main__':
	if len(sys.argv) < 1:
		print 'Usage: ios_static_analysis.py'
		sys.exit(-1)
	main(sys.argv)	


'''
Dependencies
	Ipa installer
	paramiko


JSON example
Identifier: com.thenetfirm.mobile.wapicon.WapIcon
Version: 20180517145604
Short Version: 5.5.0
Name: CaixaBank
Display Name: ADAM_FULL
Bundle: /private/var/containers/Bundle/Application/5969A30A-AB84-4EC3-BF54-BEC1A8E848A6
Application: /private/var/containers/Bundle/Application/5969A30A-AB84-4EC3-BF54-BEC1A8E848A6/ADAM_FULL.app
Data: /private/var/mobile/Containers/Data/Application/4B8DFBBE-21AE-4012-8414-65B4007DA246
arc: 0
xml: []
sql: []
db: []
pie: 1
stack: 1
keyboard: {'ey': ['/var/mobile/Library/Keyboard/'], 'hola': ['/var/mobile/Library/Keyboard/']},
'''

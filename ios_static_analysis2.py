import os
import sys
import pxssh
import getpass
import time
import paramiko

class bcolors:
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'

# pxssh
def open_ssh_connection():
	ssh = pxssh.pxssh()
	print '\n########### Login ###########'
	#username = raw_input('  username: ')
	#hostname = raw_input('  hostname: ')
	#password = getpass.getpass('  password: ')
	username = 'root'
	hostname = '10.76.20.139'
	password = 'tetas'
	print '  Connecting...'
	ssh.login (hostname, username, password)
	print '###############################\n'
	
	return ssh

def choose_application(ssh):
	applications = []
	ssh.sendline ('ipainstaller -l') 
	ssh.prompt()
	s = ssh.before.split('\n')[1:-1]

	print '\n########### Installed Applications ###########'
	
	for i,line in enumerate(s): # the first one is the command and the second one a null 
		applications.append(line)
		print "  " + str(i) + ". " + applications[i]
	
	print '################################################\n'
	
	num = int(input('Select the application: '))
	while num < 0 or num >= len(applications):
		num = int(input('Select the application: '))

	command = 'ipainstaller -i {}'.format(str(applications[num]))
	ssh.sendline (command) 
	ssh.prompt()
	s = ssh.before
	s = s.split('\r\n')[1:-1]
	print s
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

def check_pie(ssh, app):
	#ssh.sendline ('otool -hv ' + os.path.join(app['Application'],app['Display Name'])) 
	ssh.sendline ('ls -la') 
	ssh.prompt()
	s = ssh.before

	print 'PIE'
	print s
	print 'kaka PIE'

	ssh.sendline('uptime')   # run a command
	ssh.prompt()
	s = ssh.before            # match the prompt
	print(s)

	if "PIE" in s:
		app['pie'] = 0
	else:
		app['pie'] = 1
	
	if "MH_MAGIC_64" in s:
		app['cpu'] = "ARM 64 bits"
	else:
		app['cpu'] = "ARM 32 bits"


def check_stack(ssh, app):
	#ssh.sendline ('otool -I -v ' + os.path.join(app['Application'],app['Display Name']) + ' | grep stack_chk') 
	ssh.sendline('pwd')
	ssh.prompt()
	s = ssh.before

	print 'STACK'
	print s
	print 'kaka STACK'

	if "stack_chk_guard" in s and "stack_chk_fail" in s:
		app['stack'] = 0
	else:
		app['stack'] = 1


def check_arc(ssh, app):
	ssh.sendline ('otool -I -v ' + os.path.join(app['Application'],app['Display Name']) + ' | grep _objc_') 
	ssh.prompt()
	s = ssh.before

	print 'ARC'
	print s
	print 'kaka ARC'

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


def get_files_by_extension(ssh, app, exts):
	for ext in exts:
		ssh.sendline ('find ' + app['Bundle'] + ' -iname "*.' + ext + '*"') 
		ssh.prompt()
		s = ssh.before
		
		# Es descarta la primera perque es la comanda i la ultima es un salt de linia buit
		files = s.split('\n')[1:-1] 
		app[ext] = files

'''
def convert_plist(ssh, app):
	for file in app['plist']:
		ssh.sendline ('plutil -convert xml1 -i ' + file) 
		ssh.prompt()
'''

def print_menu(options):
	print '\n########### MENU ###########'
	for i,opt in options.iteritems():
		print '  {}. {}'.format(i,opt['description'])
	print '\n  0. Exit'
	print '############################\n'

def test1(ssh,app):
	ssh.sendline ('echo "1"') 
	ssh.prompt()
	s = ssh.before

	print "test1: " + s

	ssh.sendline ('echo "2"') 
	ssh.prompt()
	s = ssh.before

	print "test1: " + s

	ssh.sendline ('echo "3"') 
	ssh.prompt()
	s = ssh.before

	print "test1: " + s

def test2(ssh,app):
	ssh.sendline ('echo "4"') 
	ssh.prompt()
	s = ssh.before

	print "test2: " + s

	ssh.sendline ('echo "5"') 
	ssh.prompt()
	s = ssh.before

	print "test2: " + s

	ssh.sendline ('echo "6"') 
	ssh.prompt()
	s = ssh.before

	print "test2: " + s


def basic_info(ssh,app):
	test1(ssh,app)
	test2(ssh,app)
	#check_pie(ssh,app)
	#check_stack(ssh,app)
	#check_arc(ssh,app)
	ext = [
		"plist",
		"sql",
		"db",
		"xml",
	]
	#get_files_by_extension(ssh,app,ext)

def option2(ssh,app):
	convert_plist(ssh,app)

def main(args):
	OPTIONS = {
		'1': {'func':basic_info,'description':'Obtain basic information'},
		'2': {'func':option2,'description':'Convert plist'},
	}

	ssh = open_ssh_connection()
	app = choose_application(ssh)
	print app
	
	option = 1
	while int(option):
		print_menu(OPTIONS)
		option = raw_input('Select an option: ')

		if option in OPTIONS:
			OPTIONS[option]['func'](ssh,app)
		else:
			pass
	
	#app = dynamic_path(ssh,app)

	
		print app

	ssh.logout


if __name__ == '__main__':
	if len(sys.argv) < 1:
		print 'Usage: ios_static_analysis.py'
		sys.exit(-1)
	main(sys.argv)	

	#option = d.get_key(arg, None)


'''
Dependencies
	Ipa installer


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

'''

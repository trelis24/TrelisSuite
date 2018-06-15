import os
import sys
import pxssh
import getpass

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
	username = raw_input('  username: ')
	hostname = raw_input('  hostname: ')
	password = getpass.getpass('  password: ')
	print '  Connecting...'
	ssh.login (hostname, username, password)
	print '###############################\n'
	
	return ssh

def choose_application(ssh):
	applications = []
	ssh.sendline ('ps aux | grep -i "[A]pplication"') 
	ssh.prompt()
	
	for line in ssh.before.split('\n')[:-1]:
		appDic = {}
		pid = line.split()[1]
		path = line.split()[-1]
		app = path.split('/')
		for s in app:
			if ".app" in s:
				appDic = {'name':s.split('.')[0], 'static_path':path.rsplit('/',1)[0], 'pid':pid}
				applications.append(appDic)
			
	print '\n########### Running applications ###########'
	
	for i, s in enumerate(applications):
		print "  " + str(i) + ". " + s['name']
	
	print '############################################\n'
	
	num = int(input('Select the application: '))
	while num < 0 or num >= len(applications):
		num = int(input('Select the application: '))
	return applications[num]


def dynamic_path(ssh, app):
	ssh.sendline ('cycript -p ' + app['pid']) 
	ssh.sendline ('[[[NSFileManager defaultManager] URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask] lastObject];') 
	ssh.prompt()

	app['dynamic_path'] = ssh.before.split('"')[1].split("file://")[1].split("Documents/")[0]

	ssh.sendline ('?exit') 
	ssh.prompt()


def check_pie(ssh, app):
	ssh.sendline ('otool -hv ' + os.path.join(app['static_path'],app['name'])) 
	ssh.prompt()
	s = ssh.before
	
	if "PIE" in s:
		app['pie'] = 0
	else:
		app['pie'] = 1
	
	if "MH_MAGIC_64" in s:
		app['cpu'] = "ARM 64 bits"
	else:
		app['cpu'] = "ARM 32 bits"


def check_stack(ssh, app):
	ssh.sendline ('otool -I -v ' + os.path.join(app['static_path'],app['name'])) 
	ssh.prompt()
	s = ssh.before

	if "stack_chk_guard" in s and "stack_chk_fail":
		app['stack'] = 0
	else:
		app['stack'] = 1


def check_arc(ssh, app):
	ssh.sendline ('otool -I -v ' + os.path.join(app['static_path'],app['name'])) 
	ssh.prompt()
	s = ssh.before

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
		ssh.sendline ('find ' + app['static_path'] + ' -iname "*.' + ext + '*"') 
		ssh.prompt()
		s = ssh.before
		
		# Es descarta la primera perque es la comanda i la ultima es un salt de linia buit
		files = s.split('\n')[1:-1] 
		app[ext] = files


def convert_plist(ssh, app):
	for file in app['plist']:
		ssh.sendline ('plutil -convert xml1 -i ' + file) 
		ssh.prompt()


def print_menu(options):
	print '\n########### MENU ###########'
	for i,opt in options.iteritems():
		print '  {}. {}'.format(i,opt['description'])
	print '\n  0. Exit'
	print '############################\n'

def basic_info(ssh,app):
	check_pie(ssh,app)
	check_stack(ssh,app)
	check_arc(ssh,app)
	ext = [
		"plist",
		"sql",
		"db",
		"xml",
	]
	get_files_by_extension(ssh,app,ext)

def option2(ssh,app):
	convert_plist(ssh,app)

def main(args):
	OPTIONS = {
		'1': {'func':basic_info,'description':'Obtain basic information'},
		'2': {'func':option2,'description':'Convert plist'},
	}

	ssh = open_ssh_connection()
	app = choose_application(ssh)

	
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

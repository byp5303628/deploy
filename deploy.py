import os
import logging

import datetime
import commands

import sys

HOME_DIR = os.getcwd()

CORE_DIR = HOME_DIR + "/trunk/web/service"
WEBAPP_DIR = HOME_DIR + "/trunk/web/webapp"

global DEPLOY_DICT 
global DEPENDENCY_LIST
global revision
global branch

def log(s):
	time = str(datetime.datetime.now())
	print "%s : %s" % (time, s)

def set_branch(name):
	global branch
	if name == "trunk":
		branch = name
	else:
		branch = "branches/%s" % name

def init():
	global DEPLOY_DICT, DEPENDENCY_LIST
	log("Begin to load setting.yaml")
	filename = "%s/setting.yaml" % HOME_DIR
	if not os.path.exists(filename):
		filename = "~/setting.yaml"
	if not os.path.exists(filename):
		log("Init Error: setting.yaml file does not exist. Please check your home or current path.")
		return False
	
	log("File Path : " + filename)
	file = open(filename, "r")
	import yaml
	temp = yaml.load(file)
	DEPLOY_DICT = temp["DEPLOY_DICT"]
	DEPENDENCY_LIST = temp["DEPENDENCY_LIST"]

	log("DEPLOY_DICT : " + str(DEPLOY_DICT))
	log("DEPENDENCY_LIST: " + str(DEPENDENCY_LIST))

	file.close()
	return True

def _check_out_revision():
	log("Revision is %s" % str(revision))
	os.system("svn checkout http://svn.artisanstate.com/svn/as2/%s -r %s > 1.log" % (branch, str(revision)))
	is_svn_checkout_failed = commands.getoutput("cat 1.log | grep 'Checked out revision'") == ""

	if is_svn_checkout_failed:
		log("Svn Checkout Failure")
		return false
	log("Svn Checkout Success")
	return True			
	
def _exec_maven_dependencies():
	if _check_out_revision() is False:
		return False

	log("Begin to execute maven install")
	for dependency in DEPENDENCY_LIST:
		os.chdir(CORE_DIR + "/" + dependency)
		log("Begin to install dependency " + dependency)
		
		os.system("mvn clean install -s ~/settings.xml > %s/install.log" % HOME_DIR)
		is_build_success = commands.getoutput("cat %s/install.log | grep 'BUILD SUCCESS'") != ""
		if is_build_success:
			log("Install %s Successfully" % dependency)
		else:
			log("Install %s Failed" % dependency)
			return False
	log("All dependencies are installed.")
	return True


def _exec_maven_packages():
	if _exec_maven_dependencies():
		log("Begin to execute maven package")
		for package in DEPLOY_DICT.values():
			os.chdir(WEBAPP_DIR + "/" + package)
			os.system("mvn clean package -Dmaven.test.skip=true -s ~/settings.xml > %s/package.log" % HOME_DIR)
			is_package_success = commands.getoutput("cat %s/package.log | grep 'BUILD SUCCESS'") != ""
			if is_package_success:
				log("Package %s Successfully" % package)
			else:
				log("Package %s Failed" % package)
				return False
		log("All packages are packaged successfully.")
		return True

def clean_up():
	os.chdir(HOME_DIR)
	os.system("rm *.log")
	os.system("rm *.war")

def process():
	log("HOME DIR is : " + HOME_DIR)
	log("CORE DIR is : " + CORE_DIR)
	log("WEBAPP DIR is : " + WEBAPP_DIR)

	log("Clean up all log and war temp files.")
	clean_up()

	if _exec_maven_packages():
		log("Move war to Home!")
		for k in DEPLOY_DICT.keys():
			os.system("cp %s/target/%s.war %s" % (WEBAPP_DIR + "/" + DEPLOY_DICT[k], k, HOME_DIR))

		sys.exit(0)
	else:
		sys.exit(-1)
	

if __name__ == "__main__":
	"""
	First argv is revision, second is branch name.
	"""
	init()
	global revision
	revision = sys.argv[1]
	set_branch(sys.argv[2])
	process()

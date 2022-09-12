import reconnecting_ftp
import ftputil
import os,time,json
from datetime import date,datetime,timezone,timedelta
from loguru import logger
from dateutil import parser
from tkinter import messagebox


#==========list ftp files and output to a txt file called ftp_info.txt=============
def list_ftp_files(path,ftp_addr,ftp_user,ftp_pass):
	start=datetime.now()
	ftp = ftputil.FTPHost(ftp_addr,ftp_user,ftp_pass)
	tmp = open("ftp_info.txt","w")
	
	logger.info("[GEN]FTP List Gen")
	for x,y,z in ftp.walk(path):
		for m in z:
			
			if z!="":
				

				ftp_file = x+"/"+m
				if ftp_file[-4::] in file_extension: # file_extension

				
					logger.info("[Found]"+ftp_file)
					tmp.write(ftp_file+"\n")
					
					
					
	tmp.close()
	elapsed = datetime.now() - start
	logger.success("[GEN]FTP List complete")
	logger.info("[Time elapsed] {}".format(elapsed))

#==========compare ftp time stamps==================================================
def gen_mod_time(ftp_addr,ftp_user,ftp_pass):
	start=datetime.now()
	sync_dict={}
	logger.info("[GEN]FTP MOD TIME Gen")
	sync_files = open("ftp_info.txt","r")

	for line in sync_files.readlines():
		line = line.strip()
		
		with reconnecting_ftp.Client(hostname=ftp_addr,port=21,user=ftp_user,password=ftp_pass) as ftp:

			timestamp = ftp.voidcmd("MDTM "+line)[4:]
			modi_time = parser.parse(timestamp)
			datetimeobj = datetime.strptime(str(modi_time),'%Y-%m-%d %H:%M:%S')
			modi_time=datetimeobj+timedelta(hours=8)
			
			if line not in sync_dict.keys():
				sync_dict.update({line:str(modi_time)})


	with open("ftp_mod.json","w") as ftp_mod_json:
		json.dump(sync_dict,ftp_mod_json)
	
	elapsed = datetime.now() - start
	logger.success("[GEN]FTP MOD TIME complete")
	logger.info("[Time elapsed] {}".format(elapsed))

#=========compare dicts================================================================
#if new file download / if not latest file download

def compare():
	logger.info("[Compare] Start")
	with open("ftp_mod_old.json","r") as a:
		last_dict=json.load(a)
	with open("ftp_mod.json") as b:

		latest_dict=json.load(b)
	text = ""
	

	for key in latest_dict.keys():
		if key in last_dict and latest_dict[key] == last_dict[key]:
			pass
		else:
			logger.info("[DIFF]"+key)
			text+=key+"\n"
			

	f=open("download.txt","w")
	f.write(text)
	f.close()
	#print(text)
	logger.success("[Compare] Done")
	





#==========download files==============================================================

def download_files(path,dest,ftp_addr,ftp_user,ftp_pass):
	
	download_dict={}
	if os.path.exists("download.txt"):
		ftp_txt = open("download.txt","r")
	else:
		ftp_txt = open("ftp_info.txt","r")


	for line in ftp_txt.readlines():
		line = line.strip()
		head,tail = os.path.split(line)
		local_dir_path = dest+head
		local_path = dest+line
		if os.path.exists(local_dir_path)==False:
			os.makedirs(local_dir_path)
		
		
		start = datetime.now()
		logger.info("[Download]"+local_path)



		with reconnecting_ftp.Client(hostname=ftp_addr,port=21,user=ftp_user,password=ftp_pass) as ftp:
	
			try:
				timestamp = ftp.voidcmd("MDTM "+line)[4:]
				modi_time = parser.parse(timestamp)
				datetimeobj = datetime.strptime(str(modi_time),'%Y-%m-%d %H:%M:%S')
				modi_time=datetimeobj+timedelta(hours=8)
				
				if line not in download_dict.keys():
					download_dict.update({line:str(modi_time)})

				file = open(local_path,"wb")
				ftp.retrbinary("RETR "+line,file.write)
				file.close()
				elapsed = datetime.now() - start
				
				logger.success("[Pass]"+local_path)

				logger.info("[Time elapsed] {}".format(elapsed))
			except Exception:
				logger.error("[Fail]"+local_path)
				pass

	if download_dict=={}:
		return
	with open("download.json","w") as download_json:
		json.dump(download_dict,download_json)

#==========main program=============================================================

if __name__ == "__main__":

#==========define url download path and destination of the files===================
	txt_info = ["ftp address:","ftp user name:","ftp password:","remote directory path:","local store path:"]

	
	
	if os.path.exists("ftp_mod_old.json"):
		os.remove("ftp_mod_old.json")
	if os.path.exists("download.txt"):
		os.remove("download.txt")

	if os.path.exists("ftp_modify.txt") == False:
		create_txt = open("ftp_modify.txt","w")
		for x in txt_info:
			create_txt.write(x+"\n")
		create_txt.close()
		messagebox.showerror(title="File not found",message="Please input info in ftp_modify.txt")
		
	else:
		ftp_pwd = open("ftp_modify.txt","r")
		a = (ftp_pwd.read()).split("\n")
		a = a[:-1]
		ftp_addr = a[0].replace("ftp address:","")
		ftp_user = a[1].replace("ftp user name:","")
		ftp_pass = a[2].replace("ftp password:","")
		path = a[3].replace("remote directory path:","")
		dest = a[4].replace("local store path:","")
		

		if ftp_addr and ftp_user and ftp_pass and path and dest !="":

		#==========define the extensions desired===========================================
			file_extension=[".JPG",".CSV",".jpg",".csv",".html",".nfo",".dmp","evtx",".DMP",".log"]
			test_extension=[".jpg"]

		#===================================================================================
			today = date.today()
			log_time = today.strftime("%y-%m-%d")
			trace = logger.add(log_time+".log")
		#=========Do not modify the code below============================================

			if os.path.exists("ftp_mod.json"):
				os.rename("ftp_mod.json","ftp_mod_old.json")
				list_ftp_files(path,ftp_addr,ftp_user,ftp_pass)
				gen_mod_time(ftp_addr,ftp_user,ftp_pass)
				compare()
				download_files(path,dest,ftp_addr,ftp_user,ftp_pass)
				
			else:
				list_ftp_files(path,ftp_addr,ftp_user,ftp_pass)
				gen_mod_time(ftp_addr,ftp_user,ftp_pass)
				download_files(path,dest,ftp_addr,ftp_user,ftp_pass)
		else:
				messagebox.showerror(title="Info missing",message="Find Blanks in ftp_modify.txt")



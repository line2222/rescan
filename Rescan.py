#coding=utf-8
#author=Cond0r@CodeScan
import socket
import threading
from concurrent import futures
from  Queue import Queue 
from sys import argv
import ipaddr
import sys
socket.setdefaulttimeout(3)
data='''
Lib:
	https://github.com/google/ipaddr-py
	https://pypi.python.org/pypi/futures
	pip install futures
Usage:
	python rescan.py -f  inputfile.txt 
	inputfile.txt:
		10.14.40.194:6379
	python rescan.py -i  192.168.1.1/24 -p 6379
'''
target_list=[]
def stdout( name):
	scanow ='[*] Scan %s.. '%(name)
	sys.stdout.write(str(scanow)+" "*20+"\b\b\r")
	sys.stdout.flush()
def extract_target(inputfile):
		global target_list
		inputdata=open(inputfile,'U').read().strip("\n").replace("\r",'').split("\n")
		for host in inputdata:
			host=host.split(":")
			if len(host)==2:
				target_list.append("%s:%s"%(host[0],host[1]))
			elif len(host)==1:
				target_list.append("%s:6379"%(host[0]))	
		return target_list	
def send_dbsize(conn):
	try:
		conn.send("PING\r\n")
		recv=conn.recv(1024)
		res= -1
		if recv.find("PONG") != -1:
			res=1   # 是redis 且不需要密码
		elif recv.find("NOAUTH") != -1:
			res=0	# 是redis 需要密码	
		return res
	except:
		return False
	
def conn_redis(args):
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.settimeout(2.0)
	args=args.split(":")
	host=args[0]
	port=int(args[1])
	try:
		client.connect((host, port))
		return client
	except:
		return False
def run_task(target):
	pwd=None
	stdout(target)
	conn=conn_redis(target)
	if conn:
		size=send_dbsize(conn)
		if size==1:
			return  "[!] Find %s Unauthorized  "% target
		elif size==0:
			pwd=check_password(conn)
			if pwd==None:
				return  "[x] Find %s password error "% target
			else:
				return  "[!] Find %s password %s "% (target,pwd)
	
def check_password(s):
	"""
		参数s：连接到redis 服务器的socket返回对象
		返回值：Redis服务器的密码字符串
			如果破解失败，则返回None
	"""
	fp=open("dict.txt")
	passwords=fp.readlines()
	fp.close()
	for pwd in passwords:
		pwd=pwd.strip()
		try:
			s.sendall("AUTH %s\r\n" % pwd)
			msg=s.recv(1024)
			if msg.find("OK") !=-1:
				return pwd
		except:
			pass
	s.close()
	return None

def main():
	targetlist=[]
	if len(argv)>2:
		if argv[1]=='-f':
			return extract_target(argv[2])
		if argv[1]=='-i':
			port=6379
			if len(argv)==5:
				port=int(argv[4])
			targets = ipaddr.IPv4Network(argv[2])
			for tar in targets:
				targetlist.append("%s:%d"%(tar,port))
			return targetlist
				
			
		
if len(argv)<3:
	print data
	exit()

target_list=main()


thread_pool = futures.ThreadPoolExecutor(max_workers=20)
for i in  thread_pool.map(run_task, target_list):
	if i!=None:
		print i

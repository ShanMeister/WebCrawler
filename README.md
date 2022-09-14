# Web crawler  
------------------------------------------------------------  
A scrapy crawler collecting government tender records.  
target website: 'http://web.pcc.gov.tw/'  
------Environment-------------------------------------------  
python-3.9  
scrapy-2.6  
scrapy_user_agents-0.1    
requests-2.27.1   
pymysql-1.0.2   
datetime-4.5    
psycopg2-binary-2.9.3   
python-dateutil-2.8.2   
------Counter-anti-bot approaches---------------------------  
(Using brute-force attack idea to send request, and avoid any situation whitch might stop spider from work)  
1. switch user agent (per request)  
2. set request delay time (per request)  
3. set retry delay time  
4. switch proxy IP (no need in this website)  

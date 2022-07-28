# Web crawler  
------------------------------------------------------------  
A scrapy crawler collecting government tender records.  
target website: 'http://web.pcc.gov.tw/'  
------Environment-------------------------------------------  
python-3.9  
scrapy-2.6.1  
request-2.28.1  
datetime-4.5  
------Counter-anti-bot approaches---------------------------  
(Using brute-force attack idea to send request, and avoid any situation whitch might stop spider from work)  
1. switch user agent (per request)  
2. set request delay time (per request)  
3. set retry delay time  
4. switch proxy IP (no need in this website)  

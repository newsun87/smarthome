#!/bin/bash
curl -s https://tw.stock.yahoo.com/classic > page.html #下載網頁但不會顯示進度條
iconv -f BIG-5 -t UTF-8 page.html > utf8.txt
str1=`cat utf8.txt | grep 上市 | awk -F "<" '{print $11}' | awk -F ">" '{print $2}'` #上市跌/漲
str2=`cat utf8.txt | grep 上市 | awk -F "<" '{print $15}'| awk -F ">" '{print $2}'` #點數
str3=`cat utf8.txt | grep 上市 | awk -F "<" '{print $18}' | awk -F ">" '{print $2}' ` #成交量
str7=`cat utf8.txt | grep 上市 | awk -F "<" '{print $7}' | awk -F ">" '{print $2}' ` #總點數
str4=`cat utf8.txt | grep 上櫃 | awk -F "<" '{print $11}' | awk -F ">" '{print $2}'` #上櫃跌/漲
str5=` cat utf8.txt | grep 上櫃 | awk -F "<" '{print $15}'| awk -F ">" '{print $2}'`  #點數
str6=` cat utf8.txt | grep 上櫃 | awk -F "<" '{print $18}' | awk -F ">" '{print $2}'` #成交量
str8=` cat utf8.txt | grep 上櫃 | awk -F "<" '{print $7}' | awk -F ">" '{print $2}' ` #總點數
stock_1='上市股票'$str1$str2'點成交量'$str3'總點數'$str7'點'
stock_2='上櫃股票'$str4$str5'點成交量'$str6'總點數'$str8'點' 
echo $stock_1'~'$stock_2


 




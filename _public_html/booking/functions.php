<?php

function message_goto($msg, $url="login.php"){
die('<script language=javascript>alert("'.$msg.'");location=("'.$url.'");</script>');
}
function redirectto($url){
die('<script language=javascript>location=("'.$url.'");</script>');
}
function message($msg){
die('<script language=javascript>alert("'.$msg.'");</script>');
}
function alert($msg){
die('<b><center><font size=+1 color=red >['.$msg.']</font></center></b>');
}
function is_number($num){
if(!is_numeric($num)){
message("Enter numeric values only");
}
}
function not_allnumber($num){
if(is_numeric($num)){
message("Field cannot have numbers only");
}
}
function check_dublicate($sql){
	$qry=mysql_query($sql);
	$count=mysql_num_rows($qry);
	if($count==1){
	message("Entry already exists. Try again");
	}
}
function row_count($sql){
	$qry=mysql_query($sql);
	$count=mysql_num_rows($qry);
	return $count;
}
function not_null($field){
if(!$field){
message("Fill all fields please");
}
}
function not_short($field){
if(strlen($field)<3){
message("Field characters too few");
}
}
function is_pass($field){
if(strlen($field)<6){
message("Password cannot be less than 6 characters");
}
}
function is_digits($element) {
if(preg_match ("/[^0-9]/", $element)){
message("Only digits are required");
}
}
function validate_string($num){
if(is_numeric($num)){
message("Enter string values");
}
}
function no_zero($zero){
if(substr($zero,0,1)==0){
message("Field cannot start with a zero. Integers only.");
}
}
function green($msg){
die('<b><center><font color=#00CC33>['.$msg.']</font></center></b>');
}
function validate_cell($cel){
$cel=trim(str_replace(" ","",$cel));
if(substr($cel,0,3)!="077" && substr($cel,0,3)!="073" && substr($cel,0,3)!="071" && substr($cel,0,3)!="086"  && substr($cel,0,3)!="078")
											{
											message('Cellphone number not valid in Zimbabwe');
											exit();
											}										
											switch(substr($cel,0,3))
											{
											case'086':
											if(strlen($cel)!=11)
											message("Cellphone number not valid for Africom Zimbabwe.");
											break;
											
											case'077':
											if(strlen($cel)!=10) 
											message("Cellphone number not valid for local subscribers.");
											break;
											
											case'071':
											if(strlen($cel)!=10) 
											message("Cellphone number not valid for local subscribers.");
											break;
											
											case'073':
											if(strlen($cel)!=10) 
											message("Cellphone number not valid for local subscribers.");	
											break;
											
											case'078':
											if(strlen($cel)!=10) 
											message("Cellphone number not valid for local subscribers.");	
											break;
																						
											default:
											message("Undefined cellphone number");
											}
}
///////If i want to read a novel a write one//////
?>
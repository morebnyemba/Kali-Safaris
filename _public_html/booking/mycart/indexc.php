<?php 
include("../databasecon.php");
session_start();
	$inv=$_SESSION['reg'];	 
$rs=mysql_query("select * from cart where invoice ='$inv'") or die(mysql_error());
$count=mysql_num_rows($rs);
while($fetch=mysql_fetch_array($rs))

{
	echo $count;
	echo $fetch['pnam'];

	}
?>
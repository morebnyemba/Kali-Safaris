
<?php include("../loj/databasecon.php");
error_reporting(0);
session_start();
$inv=$_SESSION['reg'];
$ip= $_SESSION['ip'];
$from= $_SESSION['from'];
$to=$_SESSION['to'];
 $npple=$_SESSION['npple'];
$totaldays=$_SESSION['nights'];


$differencetolocaltime=1;
$tim=date('U')-$differencetolocaltime*3600;
$time=date('H:i:s',$tim);
$dat=date('Y-m-d');
$dtime=$dat."(".$time.")";
$year=date('Y');
    



if(isset($_GET['nunit']))
{

$nunit=$_GET['nunit'];
/*echo "<script>window.location='cart.php?nunit=$nunit'</script>";*/

$differencetolocaltime=1;
$tim=date('U')-$differencetolocaltime*3600;
$time=date('H:i:s',$tim);
$dat=date('Y-m-d');
$dtime=$dat."(".$time.")";
$year=date('Y');

$query_data=mysql_query("SELECT * FROM cart WHERE invoice='$inv'") or die(mysql_error());
  $countr=mysql_num_rows($query_data);
  if($countr=="0")
  {
  $cond="1";
  }
  
  if($countr=="1")
  {
  $cond="2";
  }
  
  if($countr=="2")
  {
  $cond="3";
  }
  
  if($countr=="3")
  {
  $cond="4";
  }
  
  if($countr=="4")
  {
  $cond="5";
  }
  if($countr=="5")
  {
  $cond="6";
  }
  if($countr=="6")
  {
  $cond="7";
  }
  if($countr=="7")
  {
  $cond="8";
  }
		
	
	
							
$addfile = "INSERT INTO cart(id,yr,date,time,adrip,code,rtype,nunit,npple,price,nights,date1,date2,invoice,cond)".
           "VALUES (NULL,'$year','$date','$time','$ipp','$code','$rtype','$nunit','$npple','$total','$totaldays','$from','$to','$reg','$cond')";
mysql_query($addfile) or die(mysql_error());
?>
<script type="text/javascript" language="javascript">
alert("THANK YOU FOR SELECTING THIS PRODUCT. PLEASE SHOP MORE PRODUCTS!");
windows.location="index2.php";

</script>
		
<?php }?>
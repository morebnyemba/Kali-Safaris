
<?php include("../loj/databasecon.php");
error_reporting(0);
session_start();
$inv=$_SESSION['reg'];
$ip= $_SESSION['ip'];
$from= $_SESSION['from'];
$to=$_SESSION['to'];
 //$npple=$_SESSION['npple'];
$totaldays=$_SESSION['nights'];

?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">    
      <meta content="Royalty travel victoria falls" name="description"/>
<meta content="Royalty travel victoria falls contact, Royalty location, victoria falls travel agent,Request Service Form " name="keywords"/>
<meta content="www.royaltytravelvicfalls.com" name="author"/>
<link rel="shortlink" href="../ContactAndRequest/www.royaltytravelvicfalls.com"/>
    
      
<title>kalai safaris | Request Service Form</title>

    <link href="assets/css/font-awesome.css" rel="stylesheet">
    <!-- Bootstrap -->
    <link href="assets/css/bootstrap.css" rel="stylesheet">   
    <!-- Slick slider -->
    <link rel="stylesheet" type="text/css" href="assets/css/slick.css">    
    <!-- Date Picker -->
    <link rel="stylesheet" type="text/css" href="assets/css/bootstrap-datepicker.css">   
     <!-- Gallery Lightbox -->
    <link href="assets/css/magnific-popup.css" rel="stylesheet"> 
    <!-- Theme color -->
    <link id="switcher" href="assets/css/theme-color/default-theme.css" rel="stylesheet">     

    <!-- Main style sheet -->
    <link href="style.css" rel="stylesheet"> 
      <link href="logo.css" rel="stylesheet">    

   
    <!-- Google Fonts -->

    <!-- Prata for body  -->
    <link href='https://fonts.googleapis.com/css?family=Prata' rel='stylesheet' type='text/css'>
    <!-- Tangerine for small title -->
    <link href='https://fonts.googleapis.com/css?family=Tangerine' rel='stylesheet' type='text/css'>   
    <!-- Open Sans for title -->
    <link href='https://fonts.googleapis.com/css?family=Open+Sans' rel='stylesheet' type='text/css'>
    
    

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

  </head>
  <body>
<nav class="navbar navbar-custom navbar-fixed-top navbar-transparent" role="navigation">
        <div class="container">
          <div class="navbar-header">
            <button class="navbar-toggle" type="button" data-toggle="collapse" data-target="#custom-collapse"><span class="sr-only">Toggle navigation</span><span class="icon-bar"></span><span class="icon-bar"></span><span class="icon-bar"></span></button> 
 
   
    <?php 
	/*$rs1Z=mysql_query("SELECT distinct invoice FROM cart WHERE invoice='$inv'");
	$cnt=mysql_num_rows($rs1Z);
$tora1Z=mysql_fetch_array($rs1Z);
$inv2=$tora1Z['invoice'];*/
			   if($inv){?>
		<a class="navbar-brand mu-readmore-btn btn active" href="mycart/"  style="color:#000; font-size:18px;" ><div style="text-align:center;background-color:yellow"><strong>My Cart</strong> </div></a>
	<?php }?>
          </div>
          <div class="collapse navbar-collapse" id="custom-collapse">
            <ul class="nav navbar-nav navbar-right" style="font-size:15px">
              
             
              
               
              
             
              
              
             
            </ul>
          </div>
        </div>
      </nav>
  <!--START SCROLL TOP BUTTON -->
    <a class="scrollToTop" href="#">
      <i class="fa fa-angle-up"></i>
    </a>
   
  <!-- Start Reservation section -->
  <section id="mu-reservation" style="padding-top:10px; background-color:#fff">
    <div class="container">
      <div class="row">
         
        <div class="col-md-12">
     
          <div class="mu-reservation-area">
            <div class="mu-title">
              <span class="mu-subtitle">Request Service</span>
            </div>
          
      
 
   <a href="../"><img src="arro.png" style="border-radius:90px; width:80px;height:25px"/></a> 

 <?php  
    
$rs1=mysql_query("SELECT distinct rtype,id,pric,disc,total,code FROM property order by id asc");
while($tora1=mysql_fetch_array($rs1))
{
	$code=$tora1['code'];
	 $rtype=$tora1['rtype'];
	 $id=$tora1['id'];
	 $total=$tora1['total'];
	 
  
  
  
  ?>



<form method="post">
 <div class="col-md-12" style="height:60px;"></div>
                         <div style="font-size:34px; text-align:center"><?php echo $tora1['rtype'];?></div>
                        <div class="col-md-12" style="height:30px; border-bottom-color:#666; border-bottom-style:solid"> </div> 
 

<?php 

 $query_datar=mysql_query("SELECT * FROM room WHERE code='$code'") or die(mysql_error());
          $countr=mysql_num_rows($query_datar);

  ?>
 
  
 



<?php
	$rs=mysql_query("SELECT rtype,filename FROM propertypic WHERE rtype='$tora1[rtype]'");
$tora=mysql_fetch_array($rs);
	
	?>
                         <div class="col-md-12">
                         
                         <div class="col-md-6">
         <img src="../loj/property/<?php echo $tora['filename'];?>" class="img-responsive"/>    
                         </div>
                          <div class="col-md-6">
  <table width="100%"  border="1" style="border:thin; border-color:#000; border-radius:90px">
          
<tr class="bars1" style="height:60px"><!--<td width="5%"></td>-->
<?php
$query_dataD=mysql_query("SELECT * FROM dates WHERE date between '$from'and '$to'") or die(mysql_error());
  $countD=mysql_num_rows($query_dataD);
   while($fchrD=mysql_fetch_array($query_dataD)){
	   $ddat=$fchrD['date'];
	   
	   
	   
	   
	   ?>
	  <td width="10%" style="font-size:12px"><?php // echo $ddat;?>
      
		 
<strong style="font-size:18px"><?php  $datetime = DateTime::createFromFormat('Y-m-d',$ddat);?>
<?php echo $datetime->format('D'); ?></strong> &nbsp; 
<strong style="font-size:18px"><?php echo $datetime->format('d');?></strong>&nbsp;
<strong style="font-size:18px"><?php echo $datetime->format('M');?></strong>&nbsp;
<strong style="font-size:18px"><?php echo $datetime->format('Y');?></strong>

	  
      
      </td> 
      <?php
   }
	?>

</tr>
  <strong><?php
  while($fchr=mysql_fetch_array($query_datar)){
			$rooms=$fchr['rtype'];
			$roomcode=$fchr['code'];
			  
?></strong>


<tr class="blue" style="height:20px">

     	<!--<td class="blue" width="5%">
		<strong><?php //echo $rooms;?></strong>
        </td>-->
        <div id="refresh">
       
        <?php 
  
  $query_dataD=mysql_query("SELECT * FROM dates WHERE date between '$from' and '$to'") or die(mysql_error());
  $countD=mysql_num_rows($query_dataD);
   while($fchrD=mysql_fetch_array($query_dataD)){
	   $ddat=$fchrD['date'];
  
	   //$query_data=mysql_query("SELECT * FROM datsofocc WHERE date11='$ddat' and roomtobe='$rooms'") or die(mysql_error());
	   $query_data=mysql_query("SELECT * FROM roomtypesooccupied WHERE date(date1)='$ddat' and code='$roomcode'") or die(mysql_error());
  $count=mysql_num_rows($query_data);
  $fchff=mysql_fetch_array($query_data);
  $madat=$fchff['date1'];
  $codff=$fchff['code'];
  $stat=$fchff['state'];
  $rtype=$fchff['rtype'];

 
  ?>
            <td >
            
<?php if($count=='1'){ ?> <div style="text-align:center; width:60px;" class="mu-readmore-btn btn active" title="Already Taken / Unavailable"><i class="fa fa-lock"></i> </div>
		 <?php 
			 }else{
				 ?> <div style=" text-align:center; width:70px; font-size:11px">
             Available
            <div style="background-color:#fff" title="Available"><i class="fa fa-mark"></i></div>
             
             </div>
			 <?php 
				 }
			 
			 
			 ?> </td></div>
            <?php
   }?>
		
      
       
</tr>

<?php
}

?>  
</table> 
                          
                          
                          
                          
                          
                          <div style="height:10px;"></div>
                         
			<?php 
			$queryp=mysql_query("SELECT * FROM dates WHERE date between '$from' and '$to' order by id asc limit 1") or die(mysql_error());
  
   $fchrDp=mysql_fetch_array($queryp);
	   $ddatp=$fchrDp['date'];
		
			$query_dataprice=mysql_query("SELECT * FROM roompricesrates WHERE code='$code' and date(date1)='$ddatp'") or die(mysql_error());
  $countprice=mysql_num_rows($query_dataprice);
  $fprice=mysql_fetch_array($query_dataprice);
  $mari=$fprice['price'];
  				 
?>
<table class="table" width="100%">
<?php if($tora1['disc']==""){?>
<tr><td width="30%"></td><td width="40%"></td> <td width="30%"> <strong> $<?php echo $mari; //$tora1['total'];?></strong></td></tr>
<?php }elseif($tora1['disc']=="0"){?>
		Price: $<?php echo $mari; //$tora1['total'];?>
       <tr><td width="30%"></td><td width="40%"></td> <td width="30%"> <strong> $<?php echo $mari; //$tora1['total'];?></strong></td></tr>
      <?php }elseif($tora1['disc']>0){?> 
       <tr><td></td><td id="logs"><marquee behavior="alternate" direction="left">Discounted <?php echo $tora1['disc'];?>% </marquee></td> <td> Now: <strong> $<?php echo $mari; //$tora1['total'];?></strong></td></tr>
    <?php }?>   
        
        
<tr> <td colspan="2" style="text-align:right">
<?php if($rooms=="Riverside Venue Hire"){ ?>
Number of Hours :<?php } else{?>
Number Of Seats:
<?php }?></td>
<td  style="text-align:right">
 <input name="nunit" size="12" type="number" required>


</td></tr>
<?php if($rooms=="Riverside Venue Hire" || $rooms=="Learners special cruise package" || $rooms=="Dinner Cruise" ){ ?>

<?php } else{?>
<tr> <td colspan="2" style="text-align:right">
 Include Food & Drinks :</td>
 <td style="text-align:right">
 <input name="check_list0[]" type="checkbox" value="20">  
 </td></tr>
 <?php }?>
 
<tr> <td colspan="3" style="text-align:right">
<input class="mu-readmore-btn btn active"  type="submit" name="Sub1<?php echo $roomcode;?>" value="Add To Cart"/></td></tr>
</table>

 
					
							
							


<?php
 $Submit="Sub1".$roomcode;
 if(isset($_POST[''.$Submit.'']))
{
$nunit=$_POST['nunit'];

/*function getUserIpAddr(){
    if(!empty($_SERVER['HTTP_CLIENT_IP'])){
        //ip from share internet
        $ip = $_SERVER['HTTP_CLIENT_IP'];
    }elseif(!empty($_SERVER['HTTP_X_FORWARDED_FOR'])){
        //ip pass from proxy
        $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
    }else{
        $ip = $_SERVER['REMOTE_ADDR'];
    }
    return $ip;
}

$ipp=getUserIpAddr();*/
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
	
	if(!empty($_POST['check_list0'])){
foreach($_POST['check_list0'] as $selected0){
                                echo $selected0."</br>";
                                           }
                                 }	
	$includefood=$selected0*$nunit;
	
							
$addfile = "INSERT INTO cart(id,yr,date,time,adrip,code,rtype,nunit,npple,price,nights,date1,date2,invoice,cond,food)".
           "VALUES (NULL,'$year','$dat','$time','$ip','$code','$rooms','$nunit','$npple','$mari','$totaldays','$from','$to','$inv','$cond','$includefood')";
mysql_query($addfile) or die(mysql_error());
?>
<script type="text/javascript" language="javascript">
alert("ORDER SAVED THANK YOU!");


</script>
		
<?php }?>

</div></div>



<div style="height:10px;"></div>

 </form>

<?php
}
 
?>


            






       
        











            
          </div>
        </div>
      </div>
    </div>
  </section>  
  <!-- End Reservation section -->

  
  
  <!-- jQuery library -->
  <script src="assets/js/jquery.min.js"></script>  
  <!-- Include all compiled plugins (below), or include individual files as needed -->
  <script src="assets/js/bootstrap.js"></script>   
  <!-- Slick slider -->
  <script type="text/javascript" src="assets/js/slick.js"></script>
  <!-- Counter -->
  <script type="text/javascript" src="assets/js/simple-animated-counter.js"></script>
  <!-- Gallery Lightbox -->
  <script type="text/javascript" src="assets/js/jquery.magnific-popup.min.js"></script>
  <!-- Date Picker -->
  <script type="text/javascript" src="assets/js/bootstrap-datepicker.js"></script> 
  <!-- Ajax contact form  -->
  <script type="text/javascript" src="assets/js/app.js"></script>
 
  <!-- Custom js -->
  <script src="assets/js/custom.js"></script> 

  </body>
</html>
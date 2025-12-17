
<?php include("../../loj/databasecon.php");
error_reporting(0);
session_start();
$inv=$_SESSION['reg'];
$ip= $_SESSION['ip'];
$from= $_SESSION['from'];
$to=$_SESSION['to'];
 $npple=$_SESSION['npple'];
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
    
      
<title>kalai safaris  | booking</title>

    <!-- Favicon --
    <link rel="shortcut icon" href="assets/img/favicon.ico" type="image/x-icon">

    <!-- Font awesome -->
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
              <span class="mu-subtitle">My Cart </span>
            </div>

            <div class="mu-reservation-content" style="padding-top:0px">
              <a href="../index2.php"><img src="../arro.png" width="83" height="39"/></a>

              <div class="col-md-12">
                <div class="mu-reservation-left">
                  <form class="mu-reservation-form" id="form2" name="form2" method="post">
                  
                   <?php 
				   $rse=mysql_query("SELECT distinct invoice FROM cart WHERE invoice ='$inv'") or die(mysql_error());
				   $fetche=mysql_fetch_array($rse);
				   	
					$invoice= $fetche['invoice'];
				   
				   ?>
				   <table width="100%" align="right" cellspacing="0"  >
	<tr>
    	<td width="60%" style="text-align: right; font-size:12px; color:black"> 
          
         </td>
        <td width="30%" style="text-align: center; font-size:12px; color:black">Ref:  <?php echo $invoice;?></td>
    </tr>
    <tr>
    	<td style="text-align: right; font-size:12px; color:black"> 
       Check in:
         </td>
        <td style="text-align: center; font-size:12px; color:black"><?php echo $from?></td>
    </tr>
    
    
    <tr><td><div style="height:20px;"></div></td></tr>
</table>
				   
				   
                  
                  
                   <?php $rs=mysql_query("select * from cart where invoice ='$inv'") or die(mysql_error());
$count=mysql_num_rows($rs);
$grandtotal=0;
?>
<table width="100%" border="1" class="form-group">
<tr>
    	
        <td width="" style="font-size:12px; color:black"><strong>Event </strong></td>
        
        <td width="" style="font-size:12px; color:black"><strong>Seats/ Hours</strong></td>
        
        <td width="" style="font-size:12px; color:black"><strong>Price/Seat</strong></td>
        <td width="" style="font-size:12px; color:black"><strong>Total</strong></td>
       
    </tr>

<?php while($fetch=mysql_fetch_array($rs))
{ 

 
  
$date=$fetch['date']; 	
$tim= $fetch['time'];	
$code= $fetch['code']; 	
$rtype= $fetch['rtype']; 	
$nunit= $fetch['nunit']; 	
$npple= $fetch['npple']; 	
$price= $fetch['price']; 	
//$nights= $fetch['nights']; 	
$date1= $fetch['date1']; 	
$date2= $fetch['date2']; 	
$cond= $fetch['cond'];	
$invoice= $fetch['invoice'];
$food= $fetch['food'];	

$total=$nunit*$price+$food;
$grandtotal +=$total;

?>

<tr>
    	
        <td width="" style="font-size:14px; color:black"><?php echo $rtype;?></td>
         
        <td width="" style="font-size:14px; color:black"><?php echo $nunit;?> </td>
       
        <td width="" style="font-size:14px; color:black"><?php if($food){ echo $price+20;}else{ echo $price;}?></td>
        <td width="" style="font-size:14px; color:black"><?php echo $total;?></td>
        
    </tr>


<?php	}

?>
<tr>
    	
        <td width="" colspan="3" style="font-size:14px; color:black; text-align:right"><em>Excluding park fees</em>&nbsp;&nbsp;&nbsp; $</td>
        
        <td width="" style="font-size:18px; color:black"><strong> <?php echo $grandtotal;?></strong></td>
        
    </tr>
    
        
        
    
</table>
                    <div class="row">
                    <div class="col-md-12">
                        <div class="form-group">                        
                          <input type="email" name="email" class="form-control" placeholder="Email" required>
                        </div>
                      </div>
                       <div class="col-md-12">
                        <div class="form-group">                        
                          <input type="text" name="name" class="form-control" placeholder="Name and Surname" required>
                        </div>
                      </div>
                      <div class="col-md-12">
                        <div class="form-group">                        
                          <input type="text" name="cell" class="form-control" placeholder="Phone Number" required>
                        </div>
                      </div>
                      <div class="col-md-12">
                        <div class="form-group">                        
                          <input type="text" name="country" class="form-control" placeholder="Country" required>
                        </div>
                      </div>
                      <div class="col-md-12">
                        <div class="form-group">                        
                          <input type="text" name="adrs" class="form-control" placeholder="Address" required>
                        </div>
                      </div>
                      
                      <div class="col-md-12" style="font-size:12px">
                        <div class="form-group">
                          <textarea class="form-control" cols="30" name="msg" rows="3" placeholder="Your Message" ></textarea>
                        </div>
                      </div>

    



                      <button type="submit" name="Submit" class="mu-readmore-btn" onclick="if(!confirm('Have you verified your email adress. and other details.')){ return false;}">Submit Booking</button>
                    </div>
                    <?php
					if(isset($_POST['Submit']))
                        {
                    include("functions.php");
 $differencetolocaltime=+1;
$tim=date('U')+$differencetolocaltime*3600;
$time=date('H:i:s',$tim);
$dat=date('Y-m-d');
$dtime=$dat."(".$time.")";
$name=$_POST['name'];
$email=$_POST['email'];
$cell=$_POST['cell'];
$country=$_POST['country'];
$adrs=$_POST['adrs'];
$msg=$_POST['msg'];


if(!$name)
{
message("Enter your Full Name please");
}
if(!$email)
{
message("Enter your email adress e.g maps@live.com");
}

if(!$cell)
{
message("Enter your contact number");
}

$q1=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='1'") or die(mysql_error());
   $fc1=mysql_fetch_assoc($q1);
	
$date1=$fc1['date']; 	
$tim1= $fc1['time'];	
$code1= $fc1['code']; 	
$rtype1= $fc1['rtype']; 	
$nunit1= $fc1['nunit']; 	
$npple1= $fc1['npple']; 	
//$nights1= $fc1['nights']; 	
$date11= $fc1['date1']; 	
$date21= $fc1['date2']; 	
$cond1= $fc1['cond'];	
$invoice1= $fc1['invoice'];
$food1= $fc1['food'];
if($food1){
      $price1= $fc1['price']+20;
      $total1z=$nunit1*$price1;   
  
              }else{
                  $price1=$fc1['price'];
$total1z=$nunit1*$price1;  
              }

	   
	    $q2=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='2'") or die(mysql_error());
   $fc2=mysql_fetch_assoc($q2);
	 $date2=$fc2['date']; 	
$tim2= $fc2['time'];	
$code2= $fc2['code']; 	
$rtype2= $fc2['rtype']; 	
$nunit2= $fc2['nunit']; 	
$npple2= $fc2['npple']; 	
 	
//$nights2= $fc2['nights']; 	
$date12= $fc2['date1']; 	
$date22= $fc2['date2']; 	
$cond2= $fc2['cond'];	
$invoice2= $fc2['invoice'];
$food2= $fc2['food'];
if($food2){
      $price2= $fc2['price']+20;
      $total2z=$nunit2*$price2;   
              }else{
                  $price2=$fc2['price'];
$total2z=$nunit2*$price2;  
              }
if($total2z=='0'){
    $total2z="";
}
	    $q3=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='3'") or die(mysql_error());
   $fc3=mysql_fetch_assoc($q3);
$date3=$fc3['date']; 	
$tim3= $fc3['time'];	
$code3= $fc3['code']; 	
$rtype3= $fc3['rtype']; 	
$nunit3= $fc3['nunit']; 	
$npple3= $fc3['npple']; 	
//$price3= $fc3['price']; 	
//$nights3= $fc3['nights']; 	
$date13= $fc3['date1']; 	
$date23= $fc3['date2']; 	
$cond3= $fc3['cond'];	
$invoice3= $fc3['invoice'];
$food3= $fc3['food'];
if($food3){
      $price3= $fc3['price']+20;
      $total3z=$nunit3*$price3;   
              }else{
                  $price3=$fc3['price'];
$total3z=$nunit3*$price3;  
              }
    if($total3z=='0'){
    $total3z="";
}

	    $q4=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='4'") or die(mysql_error());
   $fc4=mysql_fetch_assoc($q4);
$date4=$fc4['date']; 	
$tim4= $fc4['time'];	
$code4= $fc4['code']; 	
$rtype4= $fc4['rtype']; 	
$nunit4= $fc4['nunit']; 	
$npple4= $fc4['npple']; 	
//$price4= $fc4['price']; 	
//$nights4= $fc4['nights']; 	
$date14= $fc4['date1']; 	
$date24= $fc4['date2']; 	
$cond4= $fc4['cond'];	
$invoice4= $fc4['invoice'];
$food4= $fc4['food'];
if($food4){
      $price4= $fc4['price']+20;
      $total4z=$nunit4*$price4;   
              }else{
                  $price4=$fc4['price'];
$total4z=$nunit4*$price4;  
              }
        if($total4z=='0'){
    $total4z="";
}
    $q5=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='5'") or die(mysql_error());
   $fc5=mysql_fetch_assoc($q5);
$date5=$fc5['date']; 	
$tim5= $fc5['time'];	
$code5= $fc5['code']; 	
$rtype5= $fc5['rtype']; 	
$nunit5= $fc5['nunit']; 	
$npple5= $fc5['npple']; 	
//$price5= $fc5['price']; 	
//$nights5= $fc5['nights']; 	
$date15= $fc5['date1']; 	
$date25= $fc5['date2']; 	
$cond5= $fc5['cond'];	
$invoice5= $fc5['invoice'];
$food5= $fc5['food'];
if($food5){
      $price5= $fc5['price']+20;
      $total5z=$nunit5*$price5;   
              }else{
                  $price5=$fc5['price'];
$total5z=$nunit5*$price5;  
              }
if($total5z=='0'){
    $total5z="";
}
	   
	    $q5=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='6'") or die(mysql_error());
   $fc6=mysql_fetch_assoc($q6);
$date6=$fc6['date']; 	
$tim6= $fc6['time'];	
$code6= $fc6['code']; 	
$rtype6= $fc6['rtype']; 	
$nunit6= $fc6['nunit']; 	
$npple6= $fc6['npple']; 	
//$price6= $fc6['price']; 	
//$nights6= $fc6['nights']; 	
$date16= $fc6['date1']; 	
$date26= $fc6['date2']; 	
$cond6= $fc6['cond'];	
$invoice6= $fc6['invoice'];
$food6= $fc6['food'];
if($food6){
      $price6= $fc6['price']+20;
      $total6z=$nunit6*$price6;   
              }else{
                  $price6=$fc6['price'];
$total6z=$nunit6*$price6;  
              }
if($total6z=='0'){
    $total6z="";
}
	    $q7=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='7'") or die(mysql_error());
   $fc7=mysql_fetch_assoc($q7);
$date7=$fc7['date']; 	
$tim7= $fc7['time'];	
$code7= $fc7['code']; 	
$rtype7= $fc7['rtype']; 	
$nunit7= $fc7['nunit']; 	
$npple7= $fc7['npple']; 	
//$price7= $fc7['price']; 	
//$nights7= $fc7['nights']; 	
$date17= $fc7['date1']; 	
$date27= $fc7['date2']; 	
$cond7= $fc7['cond'];	
$invoice7= $fc7['invoice'];
$food7= $fc7['food'];
if($food7){
      $price7= $fc7['price']+20;
      $total7z=$nunit7*$price7;   
              }else{
                  $price7=$fc7['price'];
$total7z=$nunit7*$price7;  
              }
if($total7z=='0'){
    $total7z="";
}
	    $q8=mysql_query("SELECT * FROM cart WHERE invoice ='$inv' and cond='8'") or die(mysql_error());
   $fc8=mysql_fetch_assoc($q8);
$date8=$fc8['date']; 	
$tim8= $fc8['time'];	
$code8= $fc8['code']; 	
$rtype8= $fc8['rtype']; 	
$nunit8= $fc8['nunit']; 	
$npple8= $fc8['npple']; 	
$price8= $fc8['price']; 	
//$nights8= $fc8['nights']; 	
$date18= $fc8['date1']; 	
$date28= $fc8['date2']; 	
$cond8= $fc8['cond'];	
$invoice8= $fc8['invoice'];
$food8= $fc8['food'];
if($food8){
      $price8= $fc8['price']+20;
      $total8z=$nunit8*$price8;   
              }else{
                  $price8=$fc8['price'];
$total8z=$nunit8*$price8;  
              }
if($total8z=='0'){
    $total8z="";
}





  //////////////////////////start mailing code here/////////////////////////////////////////////////
  require_once 'PHPMailer/class.smtp.php';
	require_once 'PHPMailer/class.phpmailer.php';

	//configure email
$mail = new PHPMailer();

	//$mail->IsSMTP();                                      
	$mail->Host = "mail.hostinger.com";  // specify main and backup server
	//$mail->SMTPAuth = true;     // turn on SMTP authentication
	//$mail->Username = "dzimba@womerus.com";  // SMTP username
	//$mail->Password = "edwillmaphosa1988"; // SMTP password
	//$mail->Port = "465";

	//$mail->SMTPSecure = 'ssl';

	$mail->From = "dontreply@kalaisafaris.com";
	//$mail->From = "$email";
	$mail->FromName = "$fname";
	$mail->AddReplyTo($email);
	$mail->AddAddress("reservation@kalaisafaris.com");

	$mail->WordWrap = 50;                                 // set word wrap to 50 characters
	$mail->IsHTML(true);                                  // set email format to HTML

	$mail->Subject = "NEW BOOKING REQUEST FROM $name  Ref $invoice";
	
	$body = " 
	<table width=100% align=right cellspacing=0  >
	<tr>
    	<td width=84% align=right> 
        <strong>BOOKING NUMBER :</strong>
         </td>
        <td width=16% align=right>$inv</td>
    </tr>
    <tr>
    	<td align=right> 
       <strong>Check in :</strong>
         </td>
        <td align=right>$from</td>
    </tr>
	
	
    
    <tr><td><div><br/><br/></div></td></tr>
</table>

<table width=100% align=right cellspacing=0  >
	<tr>
    	<td align=left> 
        <strong>From:</strong>$name<br/><br/>
        <strong>Email: </strong>$email<br/><br/>
		<strong>Cell: </strong>$cell<br/>
		<strong>Country: </strong>$country<br/>
         <strong>Address: </strong>$adrs<br/>
		 
         </td>
        
    </tr>
    <tr><td><div><br/><br/></div></td></tr>
</table>

  <table width=100% cellspacing=0 >
  <tr >
  		
        <td bgcolor=#CCCCCC align=center><strong>Event</strong></td>
        
		<td bgcolor=#CCCCCC align=center><strong>Seats/ Hours</strong></td>
        
        <td bgcolor=#CCCCCC align=center><strong>Price/Seat</strong></td>
        <td bgcolor=#CCCCCC align=center><strong>Total</strong></td>
	    
        
  </tr>
  
   
	    
	   <tr>
    	
        <td bgcolor=#CCCCCC align=center>$rtype1</td>
		
        <td bgcolor=#CCCCCC align=center>$nunit1 </td>
        
        <td bgcolor=#CCCCCC align=center>$price1</td>
        <td bgcolor=#CCCCCC align=center>$total1z</td>
        
    </tr>
   <tr>
      <td bgcolor=#CCCCCC align=center>$rtype2</td>
	  
        <td bgcolor=#CCCCCC align=center>$nunit2 </td>
       
        <td bgcolor=#CCCCCC align=center>$price2</td>
        <td bgcolor=#CCCCCC align=center>$total2z</td>
  </tr> 
		
	<tr>
        <td bgcolor=#CCCCCC align=center>$rtype3</td>
		
        <td bgcolor=#CCCCCC align=center>$nunit3 </td>
        
        <td bgcolor=#CCCCCC align=center>$price3</td>
        <td bgcolor=#CCCCCC align=center>$total3z</td>
  </tr>
  <tr>
       <td bgcolor=#CCCCCC align=center>$rtype4</td>
	   
        <td bgcolor=#CCCCCC align=center>$nunit4 </td>
        
        <td bgcolor=#CCCCCC align=center>$price4</td>
        <td bgcolor=#CCCCCC align=center>$total4z</td>
  </tr>
  <tr>
       <td bgcolor=#CCCCCC align=center>$rtype5</td>
	   
        <td bgcolor=#CCCCCC align=center>$nunit5 </td>
        
        <td bgcolor=#CCCCCC align=center>$price5</td>
        <td bgcolor=#CCCCCC align=center>$total5z</td>
  </tr>
	
	<tr>
      <td bgcolor=#CCCCCC align=center>$rtype6</td>
	  
        <td bgcolor=#CCCCCC align=center>$nunit6 </td>
        
        <td bgcolor=#CCCCCC align=center>$price6</td>
        <td bgcolor=#CCCCCC align=center>$total6z</td>
  </tr>
  <tr>
      <td bgcolor=#CCCCCC align=center>$rtype7</td>
	  
        <td bgcolor=#CCCCCC align=center>$nunit7 </td>
        
        <td bgcolor=#CCCCCC align=center>$price7</td>
        <td bgcolor=#CCCCCC align=center>$total7z</td>
  </tr>
  <tr>
       <td bgcolor=#CCCCCC align=center>$rtype8</td>
	   
        <td bgcolor=#CCCCCC align=center>$nunit8 </td>
        
        <td bgcolor=#CCCCCC align=center>$price8</td>
        <td bgcolor=#CCCCCC align=center>$total8z</td>
  </tr>
	

	
  <tr>
  	<td colspan=3 align=right><em>Excluding park fees</em>   SUBTOTAL ($)</td>
    <td  bgcolor=#CCCCCC align=center><strong>$grandtotal</strong></td>
	 
  </tr>
  
 
  </table>
  <div><br/><br/><br/></div>
  <table>
        <tr> 
        
        <td><strong>MESSAGE</strong><BR/> <P>$msg</P></td>
        </tr>
        
             </table>

	                   ";

$mail->Body    = $body;

	if(!$mail->Send())
	{
		echo "<script>alert('Email could not be sent');</script>";
	}else{
		//echo "Message sent";
		echo "<script>alert('Request sent successfully');</script>";
	}

  /////////////////////////end mailing code here///////////////////////////////////////////////////
    message("THANK YOU [".$fname."] FOR MAKING A BOOKING REQUEST. WE WILL CONTACT YOU THROUGH YOUR EMAIL [".$email."] FOR MORE CONFIRMATION");

}

 
 ?>
                    
                  </form>    
                </div>
              </div>

              
            </div>
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

<?php include("../loj/databasecon.php");
error_reporting(0);
session_start();
$inv=$_SESSION['reg'];
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
    
      
<title>Kalai Safari | Check availability</title>

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
<?php include ("../loj/uidatpic.php");?>
 
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
  <body >
<nav class="navbar navbar-custom navbar-fixed-top navbar-transparent" role="navigation">
        <div class="container">
          <div class="navbar-header">
            <button class="navbar-toggle" type="button" data-toggle="collapse" data-target="#custom-collapse"><span class="sr-only">Toggle navigation</span><span class="icon-bar"></span><span class="icon-bar"></span><span class="icon-bar"></span></button> 
 
   
    
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
  <section id="mu-reservation" style="padding-top:10px; background-color:#fff;">
    <div class="container">
      <div class="row">
          
             <div style="padding-top:130px;"></div>
              
        <div class="col-md-12">
            <a href="../" title="Back"><img src="arro.png" style="border-radius:90px; width:80px;height:25px"/></a> 
          <div class="mu-reservation-area">
            <div class="mu-title">
            
              <span class="mu-subtitle">Check Availability</span>
            </div>
            <div style="padding-top:130px;"></div>
            <div class="container">
 
  <form name="form1" method="post" oninput="to.value = parseInt(from.value)">
  <table width="100%" style="text-align:center">
  <tr>
  <td><strong>DATE:</strong> <input name="from" type="text" onClick="ds_sh(this);" value="<?php echo $d ?>"  style="cursor: text;height:40px" id="from"></td>
  <!--<td>To: <input name="to" type="text" onClick="ds_sh(this);" value="<?php //echo $d2 ?>" style="cursor: text;height:40px" id="to"></td>-->
 
  </tr>
  
   <!--<tr>
  <td colspan="2" style="text-align:center"><div style="height:30px"></div>
   Number of Guests: <input name="npple" type="number" >
   </td> 
    
  </tr>-->
  <tr >
  <td style="text-align:center" colspan="2">
  <div style="height:60px"></div>
  <input type="submit" name="Submit" class="mu-readmore-btn btn active" value="CHECK NOW!"/></td>
  </tr>
  </table>  
</form> 
<?php if(isset($_POST['Submit'])){
	$from=$_POST['from'];
	$to=$_POST['from'];
	//$npple=$_POST['npple'];
	$night=$_POST['night'];
			$from1=strtotime($from);
			$to1=strtotime($to);
			$datediff=$to1-$from1;
			$totaldays= round($datediff/(60*60*24));
			
			function getUserIpAddr(){
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

$ipp=getUserIpAddr();



		$characters = 'ABCDEFGHIJKLMNPQRSTUVWXYZ';
	$numbers ="10000000000546321786";
	$length = 2;
	$gore=date('Y');
	$querysch=mysql_query("select * from cart");
    $countsch=mysql_num_rows($querysch);
	$katt=$countsch+1;
	
		for ($p = 0; $p < $length; $p++) {
			$codex = $characters[mt_rand(0, strlen($characters))];
						$code1 = $characters[mt_rand(0, strlen($characters))];
			$codee .= $numbers[mt_rand(0, strlen($numbers))];
			$date=date('Y');
			$datt=date('y');
			$dated=date('d');
			$datem=date('m');
			$timee=date('s');
			
			
		}
		
		$reg= "GH".$datt.$dated.$katt.$timee.$codee;

	
			
			
			 session_start();
	      $_SESSION['from'] = $_POST['from'];
		  $_SESSION['to'] = $_POST['from'];
		  //$_SESSION['npple'] = $_POST['npple'];
		  $_SESSION['nights'] = $totaldays;
		  $_SESSION['reg']=$reg;
		  $_SESSION['ip']=$ipp;
		   echo "<script>window.location='index2.php'</script>"; 
		  
		  
           ?>             

<?php }?>
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
  <!-- Date Picker --
  <script type="text/javascript" src="assets/js/bootstrap-datepicker.js"></script> 
  <!-- Ajax contact form  -->
  <script type="text/javascript" src="assets/js/app.js"></script>
 
  <!-- Custom js -->
  <script src="assets/js/custom.js"></script>
    <script src="assets/js/rangedate.js"></script>
    

  </body>
</html>
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
    
      
<title>Dzimbahwe | Request Service Form</title>

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

<div class="mu-reservation-content" style="padding-top:0px">
              

              <div class="col-md-12">
                <div class="mu-reservation-left">
                  <form class="mu-reservation-form" id="form2" name="form2" method="post">
                    <div class="row">
                      <div class="col-md-12">
                        <div class="form-group">                       
                          <input type="text" name="fname" class="form-control" placeholder="Full Name" required >
                        </div>
                      </div>
                      <div class="col-md-12">
                        <div class="form-group">                        
                          <input type="email" name="email" class="form-control" placeholder="Email" required>
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
                      ** If you have more than one room kindly specify in your message text **
                        <div class="form-group">
                          <select class="form-control" name="type" required>
                            <option value="<?php echo $_GET['rtype'];?>"><?php echo $_GET['rtype'];?></option>
                          </select>                      
                        </div>
                        
                      </div>
                      <div class="col-md-12">
                        <div class="form-group">
                          <input type="text" class="form-control" name="people"  placeholder="Number of guest" required>              
                        </div>
                      </div>
                      
                
                      <div class="col-md-12">
                        <div class="form-group">
                          <input type="text" class="form-control" name="date" id="datepicker" placeholder="Date of Arrival" required>              
                        </div>
                      </div>
                      <div class="col-md-12">
                        <div class="form-group">
                          <input type="text" class="form-control" name="date2" id="datepicker1" placeholder="Dateof departure" required>              
                        </div>
                      </div>
                      <div class="col-md-12" style="font-size:12px">
                      ** Explain what realy you want and your expectations/wish, clearly specify if you need extra rooms etc**
                        <div class="form-group">
                          <textarea class="form-control" cols="30" name="msg" rows="3" placeholder="Your Message" required></textarea>
                        </div>
                      </div>
                      <button type="submit" name="Submit" class="mu-readmore-btn" onclick="if(!confirm('Have you verified your email adress. and other details.')){ return false;}">Submit Request</button>
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
$fname=$_POST['fname'];
$email=$_POST['email'];
$cell=$_POST['cell'];
$country=$_POST['country'];
$adrs=$_POST['adrs'];
$type=$_POST['type'];
$people=$_POST['people'];
$date=$_POST['date'];
$date2=$_POST['date2'];
$msg=$_POST['msg'];


if(!$fname)
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

if(!$date)
{
message("you forgot to select date of arrival.");
}
if(!$date2)
{
message("you forgot to select date of departure.");
}
if(!$msg){
	message("Please can you kindly give us some brief description on your request so that we fully understand what you want");

	}


//// START SENDING EMAIL TO THE USER
  
$headers4="reservations@dzimbahweguestlodge.com";         
$headers.="Reply-to: $email\n";
$headers .= "From: $email\n"; 
$headers .= "Errors-to: $headers4\n"; 


 if(mail("$email","New Reservation Booking ( $type ) "," FROM : <b> $fname</b> \n\n\n  BOOKING NAME : <b>$fname</b>  \n  EMAIL : <b>$email</b> \n CELL# : <b>$cell</b> \n COUNTRY : <b>$country</b> \n ADDRESS : <b>$adrs</b> \n ROOM TYPE : <b>$type</b> \n NUMBER OF PEOPLE : <b>$people</b> \n TO CHECK IN : <b>$date</b> \n TO CHECKOUT : <b>$date2</b> \n\n \n MESSAGE  : \n\n<b>$msg</b>","$headers")){
	 echo "<center><font face='Verdana' size='2' ><b>Thank you</b> <br>Your booking details has been posted reservations desk.We will communicate through your email. </center>";
 }
 
else{ echo " <center><font face='Verdana' size='2' color=red >There is some system problem in sending  details to the email address. <br><br><input type='button' value='Retry' onClick='history.go(-1)'></center></font>";
}
	
	

	
  ////END SENDING EMAIL TO THE TEACHER
 
  /////////////////////////end mailing code here///////////////////////////////////////////////////
   // message("THANK YOU [".$fname."] FOR MAKING A REQUEST. WE WILL CONTACT YOU THROUGH YOUR EMAIL [".$email."] FOR MORE DETAILS");


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
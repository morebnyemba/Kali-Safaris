<!DOCTYPE HTML>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Home | 848 Guest House</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="" />
    <meta name="keywords" content="" />
    <meta name="author" content="" />
    <link rel="stylesheet" type="text/css" href="//fonts.googleapis.com/css?family=|Roboto+Sans:400,700|Playfair+Display:400,700">

    <link rel="stylesheet" href="css/bootstrap.min.css">
    <link rel="stylesheet" href="css/animate.css">
    <link rel="stylesheet" href="css/owl.carousel.min.css">
    <link rel="stylesheet" href="css/aos.css">
    <link rel="stylesheet" href="css/bootstrap-datepicker.css">
    <link rel="stylesheet" href="css/jquery.timepicker.css">
    <link rel="stylesheet" href="css/fancybox.min.css">
    
    <link rel="stylesheet" href="fonts/ionicons/css/ionicons.min.css">
    <link rel="stylesheet" href="fonts/fontawesome/css/font-awesome.min.css">
<?php include ("./loj/uidatpic.php");?>
    <!-- Theme Style -->
    <link rel="stylesheet" href="css/style.css">
  </head>
  <body>
    
    <header class="site-header js-site-header">
      <div class="container-fluid">
        <div class="row align-items-center">
          <div class="col-6 col-lg-4 site-logo" data-aos="fade"><a href="index.php"><img src="images/847_guest _house_logo.jpeg" height="60" width="100" alt="848 Guest House" style="border-radius:90px"/></a></div>
          <div class="col-6 col-lg-8">


            <div class="site-menu-toggle js-site-menu-toggle"  data-aos="fade">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <!-- END menu-toggle -->

            <div class="site-navbar js-site-navbar">
              <nav role="navigation">
                <div class="container">
                  <div class="row full-height align-items-center">
                    <div class="col-md-6 mx-auto">
                      <?php include('nav.php');?>
                    </div>
                  </div>
                </div>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </header>
    <!-- END head -->

   <section class="section bg-image overlay" style="background-image: url('images/counter-bg2.jpg');padding-top:110px" >
        <div class="container" >
         
            
             <h1 class="heading mb-3" style="text-align:center; color:#fff">Our Rooms</h1>
           
            
         
        </div>
      </section>
    <!-- END section -->

    <section class="section pb-4" style="padding-top:200px;">
      <div class="container">
       
        <div class="row check-availabilty" id="next">
          <div class="block-32" data-aos="fade-up" data-aos-offset="-200">
<?php
			include("./loj/databasecon.php");
error_reporting(0);
session_start();
$inv=$_SESSION['reg'];?>

            <form name="form1" method="post">
              <div class="row">
                <div class="col-md-6 mb-3 mb-lg-0 col-lg-3">
                  <label for="checkin_date" class="font-weight-bold text-black">Check In</label>
                  <div class="field-icon-wrap">
                    <div class="icon"><span class="icon-calendar"></span></div>
    <input  name="from" type="text" onClick="ds_sh(this);" value="<?php echo $d ?>"   id="checkin_date" class="form-control" required readonly>
                  </div>
                </div>
                <div class="col-md-6 mb-3 mb-lg-0 col-lg-3">
                  <label for="checkout_date" class="font-weight-bold text-black">Check Out</label>
                  <div class="field-icon-wrap">
                    <div class="icon"><span class="icon-calendar"></span></div>
     <input name="to" type="text" onClick="ds_sh(this);" value="<?php echo $d2 ?>"  id="checkout_date" class="form-control" required readonly>
                  </div>
                </div>
                <div class="col-md-6 mb-3 mb-md-0 col-lg-3">
                  <div class="row">
                    <div class="col-md-6 mb-3 mb-md-0">
                      <label for="adults" class="font-weight-bold text-black">Adults</label>
                      <div class="field-icon-wrap">
                      <input name="adults" type="number" id="adults" class="form-control" required>
                      </div>
                    </div>
                    <div class="col-md-6 mb-3 mb-md-0">
                      <label for="children" class="font-weight-bold text-black">Children</label>
                      <div class="field-icon-wrap">
                         <input name="children" type="number" id="children" class="form-control" required>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="col-md-6 col-lg-3 align-self-end">
                  <input type="submit" name="Submit"  class="btn btn-primary btn-block text-white" value="Check Availabilty" />
                </div>
              </div>
            </form>
            <?php

			
			
			 if(isset($_POST['Submit'])){
	$from=$_POST['from'];
	$to=$_POST['to'];
	
	$night=$_POST['night'];
	$adults= $_POST['adults'];
	$children=$_POST['children'];
	$npple=$adults+$children;
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
		  $_SESSION['to'] = $_POST['to'];
		  $_SESSION['adults']= $_POST['adults'];
	      $_SESSION['children']=$_POST['children'];
	    
		  $_SESSION['npple'] = $npple;
		  $_SESSION['nights'] = $totaldays;
		  $_SESSION['reg']=$reg;
		  $_SESSION['ip']=$ipp;
		   echo "<script>window.location='booking/index2.php'</script>"; 
		  
           ?>             

<?php }?>
            
            
            
           
          </div>


        </div>
      </div>
    </section>

    
    
    
    <section class="section bg-light">

      <div class="container">
        <div class="row justify-content-center text-center mb-5">
          <div class="col-md-7">
            <h2 class="heading" data-aos="fade">Great Offers</h2>
            
          </div>
        </div>
      
        <div class="site-block-half d-block d-lg-flex bg-white" data-aos="fade" data-aos-delay="100">
          <a href="#" class="image d-block bg-image-2" style="background-image: url('images/rooms/848_guest_house_family.jpg');"></a>
          <div class="text">
            </span>
            <h2 class="mb-4">Family Room</h2>
            <p>Special rooms suitable for a family looking for a holiday home, accomodating upto 4 people. The rooms are a combination of separate main bedroom with double bed and second bedroom with two separate single beds for the other two guests with inter leading doors facing opposite each other. Both rooms has got the following amenities:<strong> TV, DStv, Fridge, Working Desk,Air conditioner, Ensuite bathroom, Towels, Shared kitchen and lounge</strong></p>
            <p><a href="booking/" class="btn btn-primary text-white">Book Now</a></p>
          </div>
        </div>
        <div class="site-block-half d-block d-lg-flex bg-white" data-aos="fade" data-aos-delay="200">
          <a href="#" class="image d-block bg-image-2 order-2" style="background-image: url('images/rooms/848_guest_house_double.jpg');"></a>
          <div class="text order-1">
            
            <h2 class="mb-4">Double Room</h2>
            <p>Accommodate upto 2 people. The rooms are best designed for a comfortable holiday stay. The rooms has got following amenities: <strong>TV, DStv, Fridge, Working Desk,Air conditioner, Ensuite bathroom, Towels, Shared kitchen and lounge</strong> </p>
            <p><a href="booking/" class="btn btn-primary text-white">Book Now</a></p>
          </div>
        </div>
         <div class="site-block-half d-block d-lg-flex bg-white" data-aos="fade" data-aos-delay="100">
          <a href="#" class="image d-block bg-image-2" style="background-image: url('images/rooms/848_guest_house_single.jpg');"></a>
          <div class="text">
            </span>
            <h2 class="mb-4">Single Room</h2>
            <p>Special deluxe room suitable for a sigle guest looking for a holiday home, accomodating only one person. the room has got the following amenities:<strong> TV, DStv, Fridge, Working Desk,Air conditioner, Ensuite bathroom, Towels, Shared kitchen and lounge</strong></p>
            <p><a href="booking/" class="btn btn-primary text-white">Book Now</a></p>
          </div>
        </div>
         <div class="site-block-half d-block d-lg-flex bg-white" data-aos="fade" data-aos-delay="200">
          <a href="#" class="image d-block bg-image-2 order-2" style="background-image: url('images/rooms/848_guest_house_twin.jpg');"></a>
          <div class="text order-1">
            
            <h2 class="mb-4">Twin Room</h2>
            <p>Deluxe rooms a ccommodating upto 2 people. The rooms are best designed for a comfortable holiday stay with two separate beds. The rooms has got following amenities: <strong>TV, DStv, Fridge, Working Desk,Air conditioner, Ensuite bathroom, Towels, Shared kitchen and lounge</strong> </p>
            <p><a href="booking/" class="btn btn-primary text-white">Book Now</a></p>
          </div>
        </div>
        <div class="site-block-half d-block d-lg-flex bg-white" data-aos="fade" data-aos-delay="100">
          <a href="#" class="image d-block bg-image-2" style="background-image: url('images/rooms/848_guest_house_honeymoon.jpg');"></a>
          <div class="text">
            </span>
            <h2 class="mb-4">Honeymoon Suite</h2>
            <p>Deluxe room suitable for a Couple looking for a very nice, romantic holiday home.  The room has got the following amenities:<strong> TV, DStv, Fridge, Working Desk,Air conditioner, Ensuite bathroom, own private entrance, own veranda for relaxing.</strong></p>
            <p><a href="booking/" class="btn btn-primary text-white">Book Now</a></p>
          </div>
        </div>
        

      </div>
    </section>

     <footer class="section footer-section">
      <div class="container">
        <div class="row mb-4">
          
          <div class="col-md-4 mb-5">
            <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1898.0240226069352!2d25.820822052784088!3d-17.92991290364305!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x194fe53f0d97964b%3A0xb5064359416ab317!2sVictoria%20Falls!5e0!3m2!1sen!2szw!4v1667401230912!5m2!1sen!2szw" width="100%" height="100%" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
          </div>
          <div class="col-md-4 mb-5 pr-md-5 contact-info">
            <!-- <li>198 West 21th Street, <br> Suite 721 New York NY 10016</li> -->
            <p><span class="d-block"><span class="ion-ios-location h5 mr-3 text-primary"></span>Address:</span> <span> 848 Aerodrome <br> Victoria Falls Zimbabwe</span></p>
            <p><span class="d-block"><span class="ion-ios-telephone h5 mr-3 text-primary"></span>Call:</span> <span> (+263) 772855945</span></p>
            <p><span class="d-block"><span class="ion-ios-email h5 mr-3 text-primary"></span>Email:</span> <span> reservations@848guesthouse.com</span></p>
          </div>
          
          <div class="col-md-4 mb-5 pr-md-5 contact-info">
          
             <div id="fb-root"></div>
<script async defer crossorigin="anonymous" src="https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v14.0" nonce="KMcxWTL7"></script>
<div class="fb-page" data-href="https://www.facebook.com/profile.php?id=100083283133791" data-tabs="timeline" data-width="300" data-height="300" data-small-header="false" data-adapt-container-width="true" data-hide-cover="false" data-show-facepile="true"><blockquote cite="https://www.facebook.com/profile.php?id=100083283133791" class="fb-xfbml-parse-ignore"><a href="https://www.facebook.com/profile.php?id=100083283133791">Ultracare Home</a></blockquote></div> 
           </div>       
          
          
          
          
          
          
          
        </div>
        <div class="col-md-12" style="text-align:center">
        <div class="container">
        <div class="row">
           
             <div class="col-lg-6" style="text-align:center"> 848 Guesthouse &copy;<?php echo "2019";?> - <?php echo date('Y');?> </div>
             <div class="col-lg-6" style="text-align:right">Powered by :<a href="emzayah.com" target="_blank" >eMaps Technologies</a></div>
           
            
        </div></div>  
        </div>
      </div>
         <script  type="text/javascript">
  var config = {
    phone :" 263772855945",
    call :"Chat with Reservations",
    position :"ww-right",
    size : "ww-normal",
    text : "",
    type: "ww-standard",
    brand: "848 Guest House",
    subtitle: "",
    welcome: "Hi, There! Its my pleasure to assist you"
  };
  var proto = document.location.protocol, host = "cloudfront.net", url = proto + "//d3kzab8jj16n2f." + host;
    var s = document.createElement("script"); s.type = "text/javascript"; s.async = true; s.src = url + "/v2/main.js";

    s.onload = function () { tmWidgetInit(config) };
    var x = document.getElementsByTagName("script")[0]; x.parentNode.insertBefore(s, x);
</script>
    </footer>
    
    <script src="js/jquery-3.3.1.min.js"></script>
    <script src="js/jquery-migrate-3.0.1.min.js"></script>
    <script src="js/popper.min.js"></script>
    <script src="js/bootstrap.min.js"></script>
    <script src="js/owl.carousel.min.js"></script>
    <script src="js/jquery.stellar.min.js"></script>
    <script src="js/jquery.fancybox.min.js"></script>
    
    
    <script src="js/aos.js"></script>
    
    <!--<script src="js/bootstrap-datepicker.js"></script> 
    <script src="js/jquery.timepicker.min.js"></script> -->

    

    <script src="js/main.js"></script>
  </body>
</html>
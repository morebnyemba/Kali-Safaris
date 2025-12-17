<?php 
include("databasecon.php");
error_reporting(0);
session_start();

$inv=$_SESSION['reg'];
?>
<!DOCTYPE html>
<html lang="en-US" dir="ltr">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!--  
    Document Title
    =============================================
    -->
    <title>Products | Zim Art gallery</title>
    <!--  
    Favicons
    =============================================
    -->
    
    <link rel="icon" type="image/png" sizes="16x16" href="assets/images/favicons/favicon-16x16.png">
    <link rel="manifest" href="/manifest.json">
    <meta name="msapplication-TileColor" content="#ffffff">
    <meta name="theme-color" content="#ffffff">
    <!--  
    Stylesheets
    =============================================
    
    -->
    <!-- Default stylesheets-->
    <link href="assets/lib/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Template specific stylesheets-->
    <link href="https://fonts.googleapis.com/css?family=Roboto+Condensed:400,700" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css?family=Volkhov:400i" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700,800" rel="stylesheet">
    <link href="assets/lib/animate.css/animate.css" rel="stylesheet">
    <link href="assets/lib/components-font-awesome/css/font-awesome.min.css" rel="stylesheet">
    <link href="assets/lib/et-line-font/et-line-font.css" rel="stylesheet">
    <link href="assets/lib/flexslider/flexslider.css" rel="stylesheet">
    <link href="assets/lib/owl.carousel/dist/assets/owl.carousel.min.css" rel="stylesheet">
    <link href="assets/lib/owl.carousel/dist/assets/owl.theme.default.min.css" rel="stylesheet">
    <link href="assets/lib/magnific-popup/dist/magnific-popup.css" rel="stylesheet">
    <link href="assets/lib/simple-text-rotator/simpletextrotator.css" rel="stylesheet">
    <!-- Main stylesheet and color file-->
    <link href="assets/css/style.css" rel="stylesheet">
    <link id="color-scheme" href="assets/css/colors/default.css" rel="stylesheet">
  </head>
  <body data-spy="scroll" data-target=".onpage-navigation" data-offset="60">
   <form id="form1" name="form1" method="post" action="">
  <?php include("databasecon.php");
   if(isset($_GET['pachiri'])){
	$id = $_GET['pachiri'];
	$code = $_GET['code'];
  $query21=mysql_query("select * from schools where id='$id' and nid='$code' and cond=''") or die(mysql_error());
                                    $fetch21=mysql_fetch_array($query21);
									$codek=$fetch21['code'];
									$agentnam=$fetch21['agentnam'];
									$asscntry=$fetch21['asscntry'];
									$dist=$fetch21['dist'];
									$prov=$fetch21['prov'];
									$email=$fetch21['email'];
									$adr=$fetch21['adr'];
									$cell=$fetch21['cell'];
									$yr=$fetch21['yr'];
									$date=$fetch21['date'];
									$level=$fetch21['level'];
									$nid=$fetch21['nid'];
									$pnam=$fetch21['pnam'];
									$matype=$fetch21['matype'];
									$color=$fetch21['color'];
									$price=$fetch21['price'];
									$lwh=$fetch21['lwh'];
									$wgt=$fetch21['wgt'];
									$type=$fetch21['type'];
									$promo=$fetch21['promo'];
									$qty=$fetch21['qty'];
									$image=$fetch21['image'];
									$msg=$fetch21['msg'];
						?>			
  
    <main>
      <!--<div class="page-loader">
        <div class="loader">Loading...</div>
      </div>-->
      
      <?php include('nav.php');?>
      <div class="main">
         
        <section class="module">
  
          <div class="container">
            <div class="row">
            <h1 style="text-align:center;color:#000; font-size:20px;" class="work-details-title font-alt"><strong><?php echo ucwords($pnam);?></strong></h1>
          
              <div class="col-sm-6 col-md-8 col-lg-8">
          
                <div class="post-images-slider">
                <ul class="slides">
                <?php $query21f=mysql_query("select * from schools where nid='$nid'") or die(mysql_error());
                                    while($fetch21f=mysql_fetch_array($query21f)){?>
                    <li><img class="center-block" src="comprihension/<?php echo $fetch21f['image'];?>" alt="Slider Image" style="border-style:solid; border-width:2px; border-color:#FF0"/></li>
                    <?php }?>
                 
                 
                 
                  </ul>
                </div>
                
              </div>
              <div class="col-sm-6 col-md-4 col-lg-4">
                <div class="work-details">
                  
                  <h5 class="work-details-title font-alt"><strong>SUMMARY DESCRIPTION</strong> </h5>
                  <p style="font-size:15px"><?php echo $msg;?></p>
                  <ul>
<li style="font-size:14px; color:#000"><strong>Material Type: </strong><span class="font-serif"><a href="#" style="font-size:14px; color:#000"><?php echo $matype;?> </a></span>
                    </li>
           <li style="font-size:14px; color:#000"><strong>Colour: </strong><span class="font-serif"><a href="#"style="font-size:14px; color:#000" ><?php echo $color;?> </a></span>
                    </li>
               <li style="font-size:14px; color:#000"><strong>Weight: </strong><span class="font-serif"><a href="#" style="font-size:14px; color:#000"><?php echo $wgt;?> </a></span>
                    </li>
<li style="font-size:14px; color:#000"><strong>Dimensions (L x W x H): </strong><span class="font-serif"><a href="#"style="font-size:14px; color:#000"> <?php echo $lwh;?>  </a></span>
                    </li>
                    
                   <li style="font-size:14px; color:#000"><strong>Code: </strong><span class="font-serif"><?php echo $nid;?> 
                   </span></li>
                  </ul>
                  
                  <div style="border-style:double; border-color:#F00; height:30px; text-align:center"><strong style="font-size:16px"> $<?php echo $price;?> USD</strong></div>
                </div>
                <strong>make an order of</strong>
                <div class="row mb-20">
                
                  <div class="col-sm-4 mb-sm-20">
                    <input class="form-control input-lg" type="number" name="qty" value="1" max="100" min="1" required="required"/>
                  </div>
                  <div class="col-sm-8">
<!--<a class="btn btn-lg btn-block btn-round btn-b" style="background-color:green" href="cart.php?page=cart.php&&pachiri=<?php //echo $fetch21['id'];?>&cde=<?php //echo $fetch21['nid'];?>">Add To Cart</a>-->
<input class="btn btn-lg btn-block btn-round btn-b" style="background-color:green; z-index:50px" type="submit" name="Submit" value="Add To Cart"/>

<button type="submit" name="Submito" style="text-align:left; font-size:19px; color:#fff; background-color:#fff; height:0px "></button>
                  </div>
                </div>
              </div>
              
            </div>
            
            </div>
            </section>
            
            
           <?php 
		   if(isset($_POST['Submit']))
{



if(isset($_POST['Submit']))
{
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


if($inv){
	
		    $query21g=mysql_query("select * from cart where invoice='$inv'") or die(mysql_error());
                                    $fetch21g=mysql_fetch_array($query21g);
									$invyatorwa=$fetch21g['invoice'];
		   session_start();
	      $_SESSION['qty'] = $qtty;
		  $_SESSION['id'] = $idd;
		  $_SESSION['code'] = $proCode;
	$_SESSION['reg'] = $invyatorwa;
		   
		  
	}else{
		$characters = 'ABCDEFGHIJKLMNPQRSTUVWXYZ';
	$numbers ="10000000000546321786";
	$length = 2;
	$gore=date('Y');
	$querysch=mysql_query("select * from cart");
    $countsch=mysql_num_rows($querysch);
	$katt=$countsch+1;
	
		for ($p = 0; $p < $length; $p++) {
			$code = $characters[mt_rand(0, strlen($characters))];
						$code1 = $characters[mt_rand(0, strlen($characters))];
			$codee .= $numbers[mt_rand(0, strlen($numbers))];
			$date=date('Y');
			$datt=date('y');
			$dated=date('d');
			$datem=date('m');
			$timee=date('s');
			
		}
		
		$reg= "ZAG".$datt.$dated.$katt.$timee;

	
	
	
	
		   $qty=mysql_real_escape_string($_POST['qty']);
		   $id = $_GET['pachiri'];
	       $code = $_GET['code']; 
		   session_start();
	      $_SESSION['qty'] = $qtty;
		  $_SESSION['id'] = $idd;
		  $_SESSION['code'] = $proCode;
		  $_SESSION['reg'] = $regg;
		   
		   echo "<script>window.location='cart.php?page=cart.php'</script>";
	
	
		
		}
	
	
	
 
	
	   
       }
	   }     
   }
          ?>  
            
            
            
            </form>
            
         <section class="module sliding-portfolio" style="margin-top:-200px" >
              <h2 class="module-title font-alt" style="color:#000; font-size:20px;"><strong>OTHER RELATED ART</strong></h2>
           
          
          <div class="container-fluid">
            <div class="row">
             <div class="owl-carousel text-center" data-items="2" data-pagination="false" data-navigation="false">
             <?php $query22=mysql_query("select * from schools where level='product' and cond=''") or die(mysql_error());
                                    while($fetch22=mysql_fetch_array($query22)){
									$code22=$fetch22['code'];
									$agentnam22=$fetch22['agentnam'];
									$asscntry22=$fetch22['asscntry'];
									$dist22=$fetch22['dist'];
									$prov22=$fetch22['prov'];
									$email22=$fetch22['email'];
									$adr22=$fetch22['adr'];
									$cell22=$fetch22['cell'];
									$yr22=$fetch22['yr'];
									$date22=$fetch22['date'];
									$level22=$fetch22['level'];
									$nid22=$fetch22['nid'];
									$pnam22=$fetch22['pnam'];
									$matype22=$fetch22['matype'];
									$color22=$fetch22['color'];
									$price22=$fetch22['price'];
									$lwh22=$fetch22['lwh'];
									$wgt22=$fetch22['wgt'];
									$type22=$fetch22['type'];
									$promo22=$fetch22['promo'];
									$qty22=$fetch22['qty'];
									$image22=$fetch22['image'];
									$msg22=$fetch22['msg'];
 
           ?>
                <div class="owl-item">
                  <div class="col-sm-12">
                    <div class="work-item" ><a href="zag_product.php?pachiri=<?php echo $fetch22['id'];?>&code=<?php echo $fetch22['nid'];?>">
              <div class="work-image post-images-slider"><img src="comprihension/<?php echo $fetch22['image'] ;?>" alt="Portfolio Item"/></div>
                        <div class="work-caption font-alt">
                          <h3 class="work-title"><strong><?php echo $fetch22['pnam'] ;?></strong></h3>
                          <div class="work-title"><strong>$<?php echo $fetch22['price'] ;?></strong></div>
                        </div></a>
                        </div>
                  </div>
                </div>
                <?php }?>
              </div>
            </div>
          </div>
        </section>   
            
            
          </div>
        </section>
       
      
          
        <section class="module" style="margin-top:-160px" >
          <div class="container">
            <div class="row">
              <div class="col-sm-2"></div>
              <div class="col-sm-8" style="text-align:center">
                <h1 class="font-alt"  style="text-align:center" ><b style="color:#000; font-size:20px;">OUR ESSENCE</b></h1>
                
                <div style="font-size:15px;color:#000;">We pride ourselves in the creativity of our people, their absolute determination to tell the tales of Africa in a way only they can and the dignity of being in the frontlines of working together to bring this story to you. It is our hope that every bit of art from our gallery will bring with it a piece of the essence of our being. </div>
                <div class="module-subtitle font-serif" style="color:#000; font-size:17px">From Our World to Yours!</div>
              </div>
               <div class="col-sm-2"></div>
            </div>
          </div>
        </section>
        
    
        <div class="module-small" style="margin-top:-220px ">
          <div class="container">
            <div class="row">
              <div class="col-sm-3">
                <div class="widget">
                  <h5 class="widget-title font-alt" style="color:#000"><strong>Contact Zim Art Gallery</strong></h5>
                
                  <p style="font-size:15px;color:#000">
                 <strong> Call / Whatsapp:</strong><br/> +263 772 431 812<br/>
                                     +263 774 214 904<br/>
                  <strong>Email:</strong><a href="#">info@zimartgallery.com</a><br/>
                 <strong> Address:</strong> <br/>4759  Pioneer Road <br/>Chinotimba T/Ship<br/> Victoria Falls<br/> Zimbabwe Africa
                  </p>
                
                </div>
              </div>
              <div class="col-sm-6">
                <div class="widget"  style="text-align:center">
                  <h5 class="widget-title font-alt" style="color:#000"><strong>Office Location</strong></h5>
            <iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d7591.288987601888!2d25.8204724!3d-17.9487279!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTfCsDU2JzU0LjkiUyAyNcKwNDknMjguMiJF!5e0!3m2!1sen!2szw!4v1568731383901!5m2!1sen!2szw" width="250" height="250" frameborder="0" style="border:0;" allowfullscreen=""></iframe>
                </div>
              </div>
              
              <div class="col-sm-3">
              
                <div class="widget">
                  <h5 class="widget-title font-alt" style="color:#000"><strong>Socialise with us</strong></h5>
                  
                  <div style="border-style:solid; border-width:2px; border-color:#FF0" class="fb-page" data-href="https://www.facebook.com/dzimbahweguestlodge/" data-tabs="timeline" data-width="450" data-height="550" data-small-header="false" data-adapt-container-width="true" data-hide-cover="false" data-show-facepile="false"><blockquote cite="https://www.facebook.com/dzimbahweguestlodge/" class="fb-xfbml-parse-ignore"><a href="https://www.facebook.com/dzimbahweguestlodge/">ZIM ART GALLERY</a></blockquote></div>
                  
   <div class="footer-social-links"><a href="#"><i class="fa fa-twitter" style="font-size:30px; color:green"></i></a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
               <a href="#"><i class="fa fa-linkedin" style="font-size:30px; color:green"></i></a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
               <a href="#"><i class="fa fa-instagram" style="font-size:30px; color:green"></i></a>
                </div>         
                  
            
                </div>
              </div>
            </div>
          </div>
        </div>
        <hr class="divider-d">
        <footer class="footer " style="background-color:green">
          <div class="container">
            <div class="row">
              <div class="col-sm-3">
                <div class="footer-social-links"><a href="index2.php"><i class="fa fa-home"></i>ADMIN</a> 
                </div>
                </div>
              <div class="col-sm-9" style="text-align:center;color:#fff">
                <p class="copyright font-alt" style="color:#fff">&copy; <?php echo date('Y');?>&nbsp;<a href="index.php" style="color:#fff">zimartgallery</a></p>
              </div>
              
              </div>
            </div>
          </div>
        </footer>
      </div>
      <div class="scroll-up"><a href="#totop"><i class="fa fa-angle-double-up"></i></a></div>
    </main>
        <?php //include('footer.php') ;?>
    <!--  
    JavaScripts
    =============================================
    -->
    <script src="assets/lib/jquery/dist/jquery.js"></script>
    <script src="assets/lib/bootstrap/dist/js/bootstrap.min.js"></script>
    <script src="assets/lib/wow/dist/wow.js"></script>
    <script src="assets/lib/jquery.mb.ytplayer/dist/jquery.mb.YTPlayer.js"></script>
    <script src="assets/lib/isotope/dist/isotope.pkgd.js"></script>
    <script src="assets/lib/imagesloaded/imagesloaded.pkgd.js"></script>
    <script src="assets/lib/flexslider/jquery.flexslider.js"></script>
    <script src="assets/lib/owl.carousel/dist/owl.carousel.min.js"></script>
    <script src="assets/lib/smoothscroll.js"></script>
    <script src="assets/lib/magnific-popup/dist/jquery.magnific-popup.js"></script>
    <script src="assets/lib/simple-text-rotator/jquery.simple-text-rotator.min.js"></script>
    <script src="assets/js/plugins.js"></script>
    <script src="assets/js/main.js"></script>
    
   
    
    


  </body>
</html>
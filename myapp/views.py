from django.shortcuts import render,redirect
from .models import Contact,User,Product,Wishlist,Cart,Transaction
from django.core.mail import send_mail
import random
from django.conf import settings
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
# Create your views here.


def initiate_payment(request):
    try:
       
        amount = int(request.POST['amount'])
        user=User.objects.get(email=request.session['email'])
        carts=Cart.objects.filter(user=user)
        for i in carts:
        	i.status="paid"
        	i.save()
        
    except:
        return render(request, 'pay.html', context={'error': 'Wrong Accound Details or amount'})

    transaction = Transaction.objects.create(made_by=user,amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(transaction.made_by.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://localhost:8000/cart/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()

    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
            return render(request, 'callback.html', context=received_data)
        return render(request, 'callback.html', context=received_data)

def index(request):
	return render(request,'index.html')

def seller_index(request):
	return render(request,'seller_index.html')

def contact(request):
	if request.method=="POST":		
		Contact.objects.create(
				name=request.POST['name'],
				email=request.POST['email'],
				mobile=request.POST['mobile'],
				remarks=request.POST['remarks'],
			)
		msg="Contact Saved Successfully"
		c=Contact.objects.all().order_by('-id')
		return render(request,'contact.html',{'msg':msg,'contacts':c})
	else:
		c=Contact.objects.all().order_by('-id')
		return render(request,'contact.html',{'contacts':c})

def signup(request):
	if request.method=="POST":

		try:
			user=User.objects.get(email=request.POST['email'])
			if user:
				msg1="Email Id Already Registered"
				return render(request,'signup.html',{'msg1':msg1,'user':user})
		except:
			if request.POST['password']==request.POST['cpassword']:
				User.objects.create(
					fname=request.POST['fname'],
					lname=request.POST['lname'],
					email=request.POST['email'],
					mobile=request.POST['mobile'],
					address=request.POST['address'],
					password=request.POST['password'],
					cpassword=request.POST['cpassword'],
					usertype=request.POST['usertype']
				)
				msg="Signup Successfully"
				return render(request,'login.html',{'msg':msg})
			else:
				msg="Password & Confirm Password Does Not Matched"
				return render(request,'signup.html',{'msg':msg})
	else:
		print("Get Method Called")
		return render(request,'signup.html')

def login(request):
	if request.method=="POST":

		try:
			user=User.objects.get(email=request.POST['email'],password=request.POST['password'])
			if user.usertype=="user":
				request.session['fname']=user.fname
				request.session['email']=user.email
				wishlists=Wishlist.objects.filter(user=user)
				request.session['wishlist']=len(wishlists)
				carts=Cart.objects.filter(user=user)
				request.session['cart']=len(carts)
				return render(request,'index.html')
			elif user.usertype=="seller":
				request.session['fname']=user.fname
				request.session['email']=user.email
				return render(request,'seller_index.html')
			else:
				pass
		except:
			msg="Email Or Password Is Incorrect"
			return render(request,'login.html',{'msg':msg})
	else:
		print("Get Method Called")
		return render(request,'login.html')

def logout(request):

	try:
		del request.session['fname']
		del request.session['email']
		return render(request,'login.html')
	except:
		pass

def change_password(request):
	if request.method=="POST":
		
		user=User.objects.get(email=request.session['email'])
		if user.password==request.POST['old_password']:

			if request.POST['new_password']==request.POST['cnew_password']:

				if request.POST['old_password']!=request.POST['new_password']:

					user.password=request.POST['new_password']
					user.cpassword=request.POST['new_password']
					user.save()
					return redirect('logout')

				else:

					msg="New Password Can Not Be Your Old Password"
					return render(request,'change_password.html',{'msg':msg})	

			else:

				msg="New Password & Confirm New Password Does Not Matched"
				return render(request,'change_password.html',{'msg':msg})

		else:

			msg="Old Password Does Not Matched"
			return render(request,'change_password.html',{'msg':msg})

	else:
		return render(request,'change_password.html')

def seller_change_password(request):
	if request.method=="POST":
		
		user=User.objects.get(email=request.session['email'])
		if user.password==request.POST['old_password']:

			if request.POST['new_password']==request.POST['cnew_password']:

				if request.POST['old_password']!=request.POST['new_password']:

					user.password=request.POST['new_password']
					user.cpassword=request.POST['new_password']
					user.save()
					return redirect('logout')

				else:

					msg="New Password Can Not Be Your Old Password"
					return render(request,'seller_change_password.html',{'msg':msg})	

			else:

				msg="New Password & Confirm New Password Does Not Matched"
				return render(request,'seller_change_password.html',{'msg':msg})

		else:

			msg="Old Password Does Not Matched"
			return render(request,'seller_change_password.html',{'msg':msg})

	else:
		return render(request,'seller_change_password.html')

def forgot_password(request):
	if request.method=="POST":
		
		try:
			user=User.objects.get(email=request.POST['email'])
			if user:
				rec=[request.POST['email'],]
				subject=" OTP for Forgot Password "
				otp=random.randint(1000,9999)
				massage="Your OTP for Forgot Password Is "+str(otp)
				email_from = settings.EMAIL_HOST_USER
				send_mail(subject,massage,email_from,rec)
				return render(request,'otp.html',{'otp':otp,'email':request.POST['email']})
		except:
			pass
	else:
		return render(request,'forgot_password.html')

def verify_otp(request):
	if request.method=="POST":

		if request.POST['user_otp']==request.POST['otp']:
			return render(request,'enter_new_password.html',{'email':request.POST['email']})
		else:
			msg="Invalid OTP"
			return render(request,'otp.html',{'otp':request.POST['otp'],'email':request.POST['email'],'msg':msg})
	else:
		pass

def new_password(request):

	user=User.objects.get(email=request.POST['email'])
	if request.POST['new_password']==request.POST['cnew_password']:
		user.password=request.POST['new_password']
		user.cpassword=request.POST['new_password']
		user.save()
		return redirect('login')
	else:
		msg="New Password & Confirm New Password Does Not Matched"
		return render(request,'enter_new_password.html',{'msg':msg,'email':request.POST['email']})

def seller_add_product(request):
	if request.method=="POST":

		Product.objects.create(
				product_category=request.POST['product_category'],
				product_size=request.POST['product_size'],
				product_name=request.POST['product_name'],
				product_price=request.POST['product_price'],
				product_desc=request.POST['product_desc'],
				product_image=request.FILES['product_image'],
				product_seller=User.objects.get(email=request.session['email']),
			)
		msg="Product Added Successfully"
		return render(request,'seller_add_product.html',{'msg':msg})
	else:
		return render(request,'seller_add_product.html')

def seller_view_products(request):
	user=User.objects.get(email=request.session['email'])
	products=Product.objects.filter(product_seller=user)
	return render(request,'seller_view_products.html',{'products':products})

def seller_product_detail(request,pk):
	product=Product.objects.get(pk=pk)
	return render(request,'seller_product_detail.html',{'product':product})

def seller_edit_product(request,pk):
	if request.method=="POST":
		product=Product.objects.get(pk=pk)
		product.product_size=request.POST['product_size']
		product.product_name=request.POST['product_name']
		product.product_price=request.POST['product_price']
		product.product_desc=request.POST['product_desc']
		try:
			product.product_image=request.FILES['product_image']
		except:
			pass
		product.save()
		msg="Product Updated Successfully"
		return render(request,'seller_product_detail.html',{'product':product,'msg':msg})
	else:
		product=Product.objects.get(pk=pk)
		return render(request,'seller_edit_product.html',{'product':product})

def seller_delete_product(request,pk):
	product=Product.objects.get(pk=pk)
	product.delete()
	return redirect('seller_view_products')

def user_view_product(request,pn):
	products=Product.objects.filter(product_category=pn)
	return render(request,'user_view_product.html',{'products':products})

def user_product_detail(request,pk):
	flag=True
	flag1=True
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	try:
		Wishlist.objects.get(user=user,product=product)
		flag=False
	except:
		pass

	try:
		Cart.objects.get(user=user,product=product)
		flag1=False
	except:
		pass
	return render(request,'user_product_detail.html',{'product':product,'flag':flag,'flag1':flag1})

def add_to_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Wishlist.objects.create(user=user,product=product)
	return redirect('wishlist')

def wishlist(request):
	user=User.objects.get(email=request.session['email'])
	wishlists=Wishlist.objects.filter(user=user)
	request.session['wishlist']=len(wishlists)
	return render(request,'wishlist.html',{'wishlists':wishlists})

def remove_from_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	wishlist=Wishlist.objects.get(user=user,product=product)
	wishlist.delete()
	return redirect('wishlist')

def add_to_cart(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Cart.objects.create(user=user,product=product,price=product.product_price,net_price=product.product_price)
	return redirect('cart')

def cart(request):
	total_price=0
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,status="pending")
	request.session['cart']=len(carts)
	for i in carts:
		total_price=total_price+int(i.net_price)
	return render(request,'cart.html',{'carts':carts,'total_price':total_price})

def remove_from_cart(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	cart=Cart.objects.get(user=user,product=product)
	cart.delete()
	return redirect('cart')

def change_qty(request):
	user=User.objects.get(email=request.session['email'])
	product=Product.objects.get(pk=request.POST['product'])
	cart=Cart.objects.get(user=user,product=product)
	qty=int(request.POST['qty'])
	cart.qty=qty
	cart.net_price=int(cart.price)*qty
	cart.save()
	return redirect('cart')
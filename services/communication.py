import requests

#to authenticate user 
def login():
    response = requests.post('http://127.0.0.1:5000/auth',json={"id":1,"username":"admin","password":"admin"})
    if response.status_code == 200:
        return "authentication successful"
    else:
        return "authentication failed"
print(login())

#to get all products from products database
def getAllProducts():
    response = requests.get('http://127.0.0.1:5000/getSomeDetails',json={"id":1})
    if response.status_code == 200:
        return "Details retrieved"
    else:
        return "Specify correct id of the user"
print(getAllProducts())

#to add products to the products database
# def addProducts():
#     response = requests.post('http://127.0.0.1:5000/addProducts', json={"id":2,"title":"macbook","brand":"apple","price": 80000,"descrip":"a laptop"})
#     if response.status_code == 200:
#         return "Product added"
#     else:
#         return "give correct details"
# print(addProducts())

#to delete a product from database
def deleteProductById():
    response = requests.post('http://127.0.0.1:5000/deleteProduct',json={"id":2})
    if response.status_code == 200:
        return "Product deleted"
    else:
        return "give correct id"
print(deleteProductById())
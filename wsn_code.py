#coding=utf-8
import serial
import urllib.parse
import http.client


def main():
  conn=http.client.HTTPConnection("api.thingspeak.com:80")#se establece una conexión cliente HTTP a través de puerto 80
  headers={"Content-type":"application/x-www-form-urlencoded","Accept":"text/plain"}#Content-type: formato de datos que envías  al servidor. Accept: tipo de contenido que el cliente HTTP aceptará
  ser=serial.Serial('/dev/ttyUSB0',19200)#Se inicia la comunicación serial, donde se establece el puerto USB que se usa y los baudios
  ser.flush()#Se limpia el buffer del puerto serial por si hay algún dato no deseado
  cont=0;#Contador para saber que los 3 nodos se han unido a la red
  #Creación de la red por parte del coordinador
  ser.write(b'ATS00=0010\r\n')
  ser.write(b'ATS02=0005\r\n')
  ser.write(b'ATS03=0000000000000005\r\n')
  ser.write(b'AT+EN\r\n') 
  while True:#Bucle que recibe información cuando los nodos se unen a la red, si recibe otra información la ignora, solo se centra en recibir la información de la conexión de los nodos
    sensor=ser.readline()
    s1=sensor.decode().strip('\r\n')#Guarda lo que se lee del puerto serie sin los caracteres \r\n para evitar problemas de que el buffer tenga basura
    s0=str(s1[27:32])#Almacena un string con la informacion del Nodo que se ha unido a la red. Ej: si el nodo 1 se une envía Nodo1
    print(s0)
    if s0=='Nodo1' or s0=='Nodo2' or s0=='Nodo3':
      cont=cont+1
     
    if cont==3:#Cuando el contador vale 3, es que los 3 nodos se han unido a la red y se puede continuar con el programa
      break
  ser.write(b'AT+BCAST:00,#\r\n')#Metodo de sincronización, cuando se envía una "#" los 3 nodos empiezan a enviar sus parámetros 
  
  while True:#La información de los nodos se sube siempre en forma de bucle infinito

    while True:#bucle para leer la información de los nodos (mensajes UCAST), si recibe otra información la ignora, solo se centra en recibir los parametros de los nodos
      sensor=ser.readline()#Se lee del puerto serial, esta función es bloqueante, por lo que si aún no hay nada en el puerto serial espera hasta que lo haya
      s1=sensor.decode().strip('\r\n')#Guarda lo que se lee del puerto serial sin los caracteres \r\n para evitar problemas, el buffer podría llenarse de basura y leer valores que no son coherentes
      s0=str(s1[0:2])#En el puerto serial los parámetros llegan como un UCAST: UCAST:000D6F00003DEF30,0A= Tem1: 26, solo tenemos que quedarnos con los mensajes UCAST que lleguen al puerto serial
      s2=str(s1[27:31])#Almacena un string con la información del parámetro que mide y el nodo (nos quedamos con la parte del UCAST que nos interesa). Ej: Tem1	Temperatura del nodo 1. Necesaria la conversión a str porque en el paso anterior había que descodificar la información del puerto serial 
      s3=str(s1[33:35])#Almacena la magnitud numérica del parámetro que se mide (para el caso de la temperatura y la humedad, los valores solo son dos dígitos
      s4=str(s1[33:37])#Almacena la magnitud numérica del LDR (4 dígitos)
      if s0=='UC':#Cuando llega un UCAST seguimos con la ejecución del código 
        break
    
    seguridad=0#Variable para asegurarnos que si llega algo al puerto serial diferente a lo esperado no se ejecute el trozo de código que hace el POST (se encuentra más abajo)
    
	#Al hacer broadcast para que se envíen datos la primera vez, no se sabe que dato llegará primero
    if s2=='Tem1' or s2=='Hum1' or s2=='LDR1' or s2=='Tem2' or s2=='Hum2' or s2=='LDR2' or s2=='Tem3' or s2=='Hum3' or s2=='LDR3':#Si hago broadcast para que me envien datos la primera vez puedo recibir datos de cualquier nodo no lo sé, depende quien envie antes

      for i in range(0,9):#Se busca identificar el parámetro que ha llegado al puerto serial
        if s2=='Tem1':
          temperature1=s3#se asigna a esta variable el valor numérico de lo leído en el puerto serial
          print("Temperature1 : ", temperature1, "C")#Se imprime en el terminal de raspberry la información recibida del puerto serial
          
        elif s2=='Hum1':
          humidity1=s3
          print("Humidity1 : ", humidity1, "%")
	  
        elif s2=='LDR1':
          ldr1=s4	
          print("LDR1 : ", ldr1, "lux")
	  	  
        elif s2=='Tem2':
          temperature2=s3
          print("Temperature2 : ", temperature2, "C")
	  
        elif s2=='Hum2':
          humidity2=s3
          print("Humidity2 : ", humidity2, "%")
	  
        elif s2=='LDR2':
          ldr2=s4	
          print("LDR2 : ", ldr2, "lux")	

        elif s2=='Tem3':
          temperature3=s3
          print("Temperature3 : ", temperature3, "C")
	  
        elif s2=='Hum3':
          humidity3=s3
          print("Humidity3 : ", humidity3, "%")
	  
        elif s2=='LDR3':
          ldr3=s4	
          print("LDR3 : ", ldr3, "lux")
		  
		#Una vez se asigna a la variable correspondiente su información se vuelve a leer del puerto serial y se sigue en el bucle hasta llegar al último elemento (8)
        if i!=8: #Cuando la i ya vale 8 y llega a este punto todos los parámetros se han obtenido, hay que recordar que antes de empezar el bucle se lee ya una vez
          while True: 
            sensor=ser.readline()
            s1=sensor.decode().strip('\r\n')
            s0=str(s1[0:2])
            s2=str(s1[27:31])
            s3=str(s1[33:35])
            s4=str(s1[33:37])
            if s0=='UC':
              break
      #Se establecen las variables que van a subirse a las diferentes gráficas (fields) de Thingspeak    
      params=urllib.parse.urlencode({'field1':temperature1,'field2':humidity1,'field3':ldr1,'field4':temperature2,'field5':humidity2,'field6':ldr2,'field7':temperature3,'field8':humidity3,'key':'N0I1P6IA0WUSXP9J'})	  
      
      if i==8:#8 debido a que todos los valores de los sensores han sido ya obtenidos
        seguridad=1#Una vez se han obtenido todos los datos de los sensores de los 3 nodos se puede habilitar la opción de hacer POST

    if seguridad==1:
	  #Se envían los datos al servidor
      conn.request("POST","/update",params,headers)#/update sirve para completar la url que se puso antes al establecer la conexión: api.thingspeak.com/update
      response=conn.getresponse()#Se espera la respuesta del servidor, recibes un valor numérico y un mensaje Ej: 200 OK ó 404 NOT_FOUND
      print(response.status,response.reason) #Se imprime la respuesta del servidor
  conn.close()#se cierra la conexión	
	
if __name__=="__main__": #comprueba que el módulo que se ejecuta es main() directamente
  main()
  

        
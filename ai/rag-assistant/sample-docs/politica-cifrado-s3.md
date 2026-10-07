# Politica de cifrado en S3

Todos los buckets del portafolio usan cifrado en reposo con SSE-KMS mediante una llave administrada por el cliente (CMK).
La rotacion automatica de la llave esta habilitada y se revisa una vez al anio como minimo.

El acceso publico esta bloqueado a nivel de bucket. Las peticiones sin TLS 1.2 o superior se deniegan con la condicion
`aws:SecureTransport` y `s3:TlsVersion`. Los administradores de la llave no pueden descifrar datos: solo los roles de
aplicacion pueden usar `kms:Decrypt`, y unicamente a traves de S3.

El bucket de logs es inmutable con S3 Object Lock en modo COMPLIANCE durante 365 dias, y despues de 90 dias los logs pasan
a Glacier Instant Retrieval para seguir disponibles de inmediato durante los 12 meses que exige PCI DSS 10.5.1.

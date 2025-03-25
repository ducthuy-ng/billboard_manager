all: certs/raspi001.cert.pem certs/server.cert.pem

certs/ca.key.pem certs/ca.cert.pem:
	openssl req -x509 -newkey rsa:2048 \
				-noenc -keyout certs/ca.key.pem \
				-out certs/ca.cert.pem -days 3650 \
				-config certs/configs/bkbillboard.vn.cnf
				

certs/raspi001.key.pem:
	openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out certs/raspi001.key.pem

certs/raspi001.csr.pem: certs/raspi001.key.pem
	openssl req -new -key certs/raspi001.key.pem -out certs/raspi001.csr.pem -addext keyUsage=keyEncipherment -config certs/configs/raspi001.ext.cnf

certs/raspi001.cert.pem: certs/raspi001.csr.pem certs/ca.key.pem certs/ca.cert.pem
	openssl x509 \
		-req -in certs/raspi001.csr.pem \
		-CA certs/ca.cert.pem -CAkey certs/ca.key.pem \
		-extfile ./certs/configs/raspi001.ext.cnf \
		-out certs/raspi001.cert.pem 


certs/server.key.pem:
	openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out certs/server.key.pem

certs/server.csr.pem: certs/server.key.pem
	openssl req -new -key certs/server.key.pem -out certs/server.csr.pem -addext keyUsage=keyEncipherment -config certs/configs/server.ext.cnf

certs/server.cert.pem: certs/server.csr.pem certs/ca.key.pem certs/ca.cert.pem
	openssl x509 \
		-req -in certs/server.csr.pem \
		-CA certs/ca.cert.pem -CAkey certs/ca.key.pem \
		-extfile ./certs/configs/server.ext.cnf \
		-out certs/server.cert.pem 

clean:
	rm -f certs/*.pem
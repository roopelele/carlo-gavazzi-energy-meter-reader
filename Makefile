all: install_requirements install finish

install_requirements:
	pip install -r requirements.txt

install:
	cp energy-reader.service /etc/systemd/system/energy-reader.service
	sed -i 's?/home/pi/carlo-gavazzi-energy-meter-reader?'`pwd`'?g' /etc/systemd/system/energy-reader.service
	systemctl daemon-reload

finish:
	$(info Installation finished. Enable systemd service with 'systemctl enable energy-reader.service')

clean:
	rm -f /etc/systemd/system/energy-reader.service


apt update
curl -sSL https://get.docker.com | sh
apt install btop python3-pip -y
git config --global user.email "hibana2077@gmail.com" && git config --global user.name "hibana2077"
VERSION=$(curl --silent https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*\d')
DESTINATION=/usr/bin/docker-compose
sudo curl -L https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-$(uname -s)-$(uname -m) -o $DESTINATION
sudo chmod 755 $DESTINATION
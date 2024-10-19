#!/bin/bash

docker stop shopping
docker stop shopping_admin
docker stop forum
docker stop gitlab

docker rm shopping
docker rm shopping_admin
docker rm forum
docker rm gitlab

# One Stop Shop
# docker load --input shopping_final_0712.tar
docker run --name shopping -p 7770:80 -d shopping_final_0712

# CMS
# docker load --input shopping_admin_final_0719.tar
docker run --name shopping_admin -p 7780:80 -d shopping_admin_final_0719

# Reddit
# docker load --input postmill-populated-exposed-withimg.tar
docker run --name forum -p 9999:80 -d postmill-populated-exposed-withimg

# GitLab
# docker load --input gitlab-populated-final-port8023.tar
docker run --name gitlab --shm-size="10g" -d -p 8023:8023 gitlab-populated-final-port8023 /opt/gitlab/embedded/bin/runsvdir-start

sleep 60

# Define your actual server hostname
YOUR_ACTUAL_HOSTNAME="http://localhost"
# Remove trailing / if it exists
YOUR_ACTUAL_HOSTNAME=${YOUR_ACTUAL_HOSTNAME%/}

# OSS
docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="${YOUR_ACTUAL_HOSTNAME}:7770"
docker exec shopping mysql -u magentouser -pMyPassword magentodb -e  "UPDATE core_config_data SET value='${YOUR_ACTUAL_HOSTNAME}:7775/' WHERE path = 'web/secure/base_url';"
docker exec shopping /var/www/magento2/bin/magento cache:flush

# Disable re-indexing of products
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalogrule_product
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalogrule_rule
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalogsearch_fulltext
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_category_product
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule customer_grid
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule design_config_grid
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule inventory
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_product_category
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_product_attribute
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule catalog_product_price
docker exec shopping /var/www/magento2/bin/magento indexer:set-mode schedule cataloginventory_stock

# CMS
docker exec shopping_admin /var/www/magento2/bin/magento setup:store-config:set --base-url="${YOUR_ACTUAL_HOSTNAME}:7780"
docker exec shopping_admin mysql -u magentouser -pMyPassword magentodb -e  "UPDATE core_config_data SET value='${YOUR_ACTUAL_HOSTNAME}:7780/' WHERE path = 'web/secure/base_url';"
docker exec shopping_admin /var/www/magento2/bin/magento cache:flush

# Forum
docker exec forum sed -i '/@RateLimit/,/)/d' /var/www/html/src/DataObject/CommentData.php
docker exec forum sed -i '/@RateLimit/,/)/d' /var/www/html/src/DataObject/SubmissionData.php
docker exec forum sed -i '/@RateLimit/,/)/d' /var/www/html/src/DataObject/UserData.php
docker exec forum bin/console cache:clear --env=prod

sleep 60

# Gitlab
docker exec gitlab sed -i "s|^external_url.*|external_url '${YOUR_ACTUAL_HOSTNAME}:8023'|" /etc/gitlab/gitlab.rb
docker exec gitlab sed -i "s/.*postgresql\['max_connections'.*/postgresql\['max_connections'\] = 2000/g" /etc/gitlab/gitlab.rb
docker exec gitlab gitlab-ctl reconfigure
docker exec gitlab gitlab-ctl restart

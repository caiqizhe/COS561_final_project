# COS561_final_project

Here is a quick demo for AccWeb:
1. Open `Predictor Extension` directory
2. Open background.js and uncomment the line 3 `var prediction_dict = {"g":[{url:"https://www.google.com/", hit_count:10, miss_count:0}]};`
3. Open Google Chrome, type `chrome://extensions/` and enable `Developer mode`
4. Load unpacked extension and choose `Predictor Extension` directory
5. SSH to the remote server `ssh -i "COS561.pem" -X ubuntu@ec2-54-167-38-140.compute-1.amazonaws.com` and the public key `COS561.pem` is in the `backend` directory. You can use your own servers, but you do need to change the `server_address` in the background.js file.
6. cd `webserver` directory and type `python3 server.py`. A HTTP simple server should run.
7. Load "www.google.com" in Chrome for multiple times. Servers get web resources from navigation.
8. Clear browsing history of Chrome.
9. In Chrome, type `omnix` and press `TAB` in address bar; this action enables clients to interact with Predictor Extension and type `g`.
10. Open `background page`in `chrome://extensions`. 
11. In Network panel, you will find all resources related to `www.google.com` are fecthed.

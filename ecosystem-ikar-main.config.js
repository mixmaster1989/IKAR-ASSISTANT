module.exports = {
  "apps": [
    {
      "name": "localtunnel-ikar-main",
      "script": "lt",
      "args": "--port 6666 --subdomain igorhook6666",
      "instances": 1,
      "autorestart": true,
      "watch": false,
      "max_memory_restart": "1G",
      "env": {
        "NODE_ENV": "production"
      },
      "error_file": "./logs/localtunnel-ikar-main-error.log",
      "out_file": "./logs/localtunnel-ikar-main-out.log",
      "log_file": "./logs/localtunnel-ikar-main-combined.log",
      "time": true
    }
  ]
};
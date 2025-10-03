module.exports = {
  apps: [
    {
      name: 'localtunnel-igorhook6666',
      script: 'lt',
      args: '--port 6666 --subdomain igorhook6666',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/localtunnel-error.log',
      out_file: './logs/localtunnel-out.log',
      log_file: './logs/localtunnel-combined.log',
      time: true
    }
  ]
}; 
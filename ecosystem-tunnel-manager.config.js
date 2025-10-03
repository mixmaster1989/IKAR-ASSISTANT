module.exports = {
  apps: [
    {
      name: 'tunnel-manager',
      script: 'scripts/localtunnel_manager.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/tunnel-manager-error.log',
      out_file: './logs/tunnel-manager-out.log',
      log_file: './logs/tunnel-manager-combined.log',
      time: true
    }
  ]
}; 
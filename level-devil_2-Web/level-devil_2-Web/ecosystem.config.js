module.exports = {
  apps: [{
    name: "fabledevil",
    script: "server.js",
    cwd: __dirname,
    exec_mode: "fork",
    instances: 1,
    env: {
      NODE_ENV: "production",
      PORT: 666,
    },
    max_memory_restart: "200M",
    exp_backoff_restart_delay: 200,
    time: true,
  }],
};

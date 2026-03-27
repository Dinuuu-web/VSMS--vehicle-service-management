// charts.js - Handle Chart.js instances and SVG Gauges

if (typeof Chart !== 'undefined') {
    // Global overrides for Chart.js Skeuomorphism styling
    Chart.defaults.color = '#e0e0e0';
    Chart.defaults.font.family = "'Share Tech Mono', monospace";
    Chart.defaults.borderColor = '#333333';
}

class SkeuomorphicGauge {
  constructor(canvasId, value, label) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.value = Math.min(Math.max(value, 0), 100);
    this.label = label;
    this.ctx = this.canvas.getContext('2d');
    
    // Auto-scale support for high-DPI displays
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
    
    // Animation state
    this.currentValue = 0;
    this.targetValue = this.value;
    
    requestAnimationFrame(this.animate.bind(this));
  }

  animate() {
    if (this.currentValue < this.targetValue) {
      this.currentValue += (this.targetValue - this.currentValue) * 0.1;
      if (this.targetValue - this.currentValue < 0.1) this.currentValue = this.targetValue;
      this.draw();
      requestAnimationFrame(this.animate.bind(this));
    } else {
        this.currentValue = this.targetValue;
        this.draw();
    }
  }

  draw() {
    const ctx = this.ctx;
    const cw = this.canvas.width;
    const ch = this.canvas.height;
    
    ctx.clearRect(0, 0, cw, ch);
    
    const centerX = cw / 2;
    const centerY = ch - 20;
    const radius = Math.min(cw, ch) / 2 - 20;

    // Background arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI);
    ctx.lineWidth = 20;
    ctx.strokeStyle = '#222';
    ctx.stroke();

    // Fill arc
    const fillPercent = this.currentValue / 100;
    const endAngle = Math.PI + (fillPercent * Math.PI);
    
    let color = '#27ae60'; // Green ok
    if(this.currentValue > 70) color = '#c0a060'; // Gold warning
    if(this.currentValue > 90) color = '#c0392b'; // Red alert

    ctx.beginPath();
    if(this.currentValue > 0) {
        ctx.arc(centerX, centerY, radius, Math.PI, endAngle);
        ctx.strokeStyle = color;
        ctx.stroke();
    }
    
    // Draw tick marks
    for (let i = 0; i <= 10; i++) {
        const tickAngle = Math.PI + (i / 10) * Math.PI;
        const startX = centerX + Math.cos(tickAngle) * (radius - 15);
        const startY = centerY + Math.sin(tickAngle) * (radius - 15);
        const endX = centerX + Math.cos(tickAngle) * (radius + 15);
        const endY = centerY + Math.sin(tickAngle) * (radius + 15);
        
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.lineWidth = i === 0 || i === 5 || i === 10 ? 3 : 1;
        ctx.strokeStyle = '#e8e8e8';
        ctx.stroke();
    }
    
    // Label and percent value
    ctx.fillStyle = '#c0a060';
    ctx.font = "bold 20px 'Share Tech Mono'";
    ctx.textAlign = 'center';
    ctx.fillText(`${Math.round(this.currentValue)}%`, centerX, centerY - 25);
    
    ctx.fillStyle = '#888888';
    ctx.font = "14px 'Orbitron'";
    ctx.fillText(`${this.label}`, centerX, centerY + 10);
  }
}

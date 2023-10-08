function timer(startTime) {
  const formatTime = (timeInSeconds) => {
    const hours = Math.floor(timeInSeconds / 3600);
    const minutes = Math.floor((timeInSeconds % 3600) / 60);
    const seconds = Math.floor(timeInSeconds % 60);

    return (
      (hours < 10 ? "0" : "") +
      hours +
      ":" +
      (minutes < 10 ? "0" : "") +
      minutes +
      ":" +
      (seconds < 10 ? "0" : "") +
      seconds
    );
  };

  return {
    currentTime: Math.floor(startTime),
    formattedTime: formatTime(startTime),

    formatTime: formatTime,

    startTimer() {
      this.updateTimer();
    },

    updateTimer() {
      this.interval = setInterval(() => {
        this.currentTime += 1;
        this.formattedTime = this.formatTime(this.currentTime);
      }, 1000);
    },

    stopTimer() {
      clearInterval(this.interval);
    },
  };
}

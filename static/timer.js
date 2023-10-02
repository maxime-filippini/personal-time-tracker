function timer() {
  return {
    startTime: 0, // Initial time in seconds
    currentTime: 0, // Current time in seconds
    formattedTime: "00:00:00", // Formatted time string

    startTimer() {
      this.startTime = Math.floor(Date.now() / 1000 - this.currentTime); // Calculate the start time
      this.updateTimer(); // Start the timer
    },

    updateTimer() {
      setInterval(() => {
        this.currentTime = Math.floor(Date.now() / 1000 - this.startTime); // Calculate the current time
        this.formattedTime = this.formatTime(this.currentTime); // Format the time
      }, 1000); // Update every second
    },

    formatTime(timeInSeconds) {
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
    },
  };
}

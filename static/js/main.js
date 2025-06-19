/**
 * Displays a notification bubble on the screen.
 * @param {string} message The message to display. Can contain HTML.
 * @param {string} type The type of notification ('success', 'error', or 'info').
 */
function showNotification(message, type = "success") {
  const container = document.getElementById("notification-container");
  if (!container) {
    console.error("Notification container not found!");
    return;
  }

  const notification = document.createElement("div");
  notification.className = `notification ${type}`;

  const messageSpan = document.createElement("span");
  messageSpan.innerHTML = message;

  const closeBtn = document.createElement("span");
  closeBtn.className = "notification-close";
  closeBtn.innerHTML = "×";

  notification.appendChild(messageSpan);
  notification.appendChild(closeBtn);
  container.appendChild(notification);

  const hide = () => {
    notification.classList.remove("show");
    setTimeout(() => {
      if (container.contains(notification)) {
        container.removeChild(notification);
      }
    }, 500);
  };

  closeBtn.addEventListener("click", hide);

  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  // Use a shorter timeout for info notifications
  const timeout = type === "info" ? 3000 : 5000;
  setTimeout(hide, timeout);
}

/**
 * Shared logic to prevent clicks on child elements from triggering parent link navigation.
 */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('[data-role="child-link"]').forEach((link) => {
    link.addEventListener("click", function (event) {
      event.stopPropagation();
    });
  });
});

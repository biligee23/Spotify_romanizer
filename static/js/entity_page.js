// Wrap the entire logic in a function to avoid polluting the global scope
(function () {
  /**
   * Analyzes an image with ColorThief and applies the extracted colors
   * as CSS variables to the root element for dynamic theming.
   */
  function runColorThief() {
    const img = document.getElementById("color-thief-img");
    if (!img) return;

    // We need to ensure the image is loaded before running ColorThief,
    // especially if the src has been changed dynamically.
    const processImage = () => {
      try {
        const colorThief = new ColorThief();
        const palette = colorThief.getPalette(img, 2);

        const primaryColor = `rgb(${palette[0].join(",")})`;
        const secondaryColor = palette[1]
          ? `rgb(${palette[1].join(",")})`
          : primaryColor;

        const root = document.documentElement;
        root.style.setProperty("--primary-color", primaryColor);
        root.style.setProperty("--secondary-color", secondaryColor);
      } catch (error) {
        console.error("ColorThief error:", error);
        // Fallback to default colors if there's an error
        const root = document.documentElement;
        root.style.setProperty("--primary-color", "#bb86fc");
        root.style.setProperty("--secondary-color", "#03dac6");
      }
    };

    // If the image is already loaded (e.g., from cache), run immediately.
    // Otherwise, add an event listener.
    if (img.complete) {
      processImage();
    } else {
      img.addEventListener("load", processImage);
      // Add an error listener as a fallback
      img.addEventListener("error", () => {
        console.error("ColorThief source image failed to load.");
        processImage(); // This will now trigger the fallback in the try/catch
      });
    }
  }

  // Attach the function to the window object to make it globally accessible
  // from other scripts.
  window.runColorThief = runColorThief;

  // Run the function on initial page load
  document.addEventListener("DOMContentLoaded", runColorThief);
})();

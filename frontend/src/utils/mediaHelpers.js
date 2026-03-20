/**
 * Audio/image encoding helpers.
 */

/**
 * Convert a Blob to a File object for FormData.
 */
export function blobToFile(blob, filename) {
  return new File([blob], filename, { type: blob.type });
}

/**
 * Get user's geolocation as a promise.
 */
export function getUserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser.'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      }),
      (error) => reject(error),
      { timeout: 10000 }
    );
  });
}

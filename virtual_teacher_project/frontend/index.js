// const loginBtn = document.getElementById("loginBtn");
const loginModal = document.getElementById("loginModal");
// const closeModal = document.getElementById("closeModal");
// const signupBtn = document.getElementById("signupBtn");
const signupModal = document.getElementById("signupModal");
// const switchToSignup = document.getElementById("switchToSignup");
// const switchToLogin = document.getElementById("switchToLogin");

document.querySelectorAll(".loginBtn").forEach((link) => {
  link.addEventListener("click", () => {
    loginModal.classList.remove("hidden");
    signupModal.classList.add("hidden");
  });
});

// closeModal.addEventListener("click", () => {
//   loginModal.classList.add("hidden");
// });

loginModal.addEventListener("click", (e) => {
  if (e.target === loginModal) {
    loginModal.classList.add("hidden");
  }
});

// switchToSignup.addEventListener("click", () => {
//   loginModal.classList.add("hidden");
//   signupModal.classList.remove("hidden");
// });

document.querySelectorAll(".signupBtn").forEach((link) => {
  link.addEventListener("click", () => {
    loginModal.classList.add("hidden");
    signupModal.classList.remove("hidden");
  });
});

signupModal.addEventListener("click", (e) => {
  if (e.target === signupModal) {
    signupModal.classList.add("hidden");
  }
});

// switchToLogin.addEventListener("click", () => {
//   signupModal.classList.add("hidden");
//   loginModal.classList.remove("hidden");
// });

// Optional: Close modal when clicking outside the box
// loginModal.addEventListener("click", (e) => {
//   if (e.target === loginModal) {
//     loginModal.classList.add("hidden");
//   }
// });

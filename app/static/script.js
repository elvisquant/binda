document.getElementById("login-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      
      const form = e.target;
      const submitBtn = document.getElementById("submit-btn");
      const btnText = document.getElementById("btn-text");
      const spinner = document.getElementById("btn-spinner");
      const messageEl = document.getElementById("message");
      
      // Reset UI
      messageEl.classList.add("hidden");
      messageEl.classList.remove("text-red-600", "text-green-600");
      submitBtn.disabled = true;
      btnText.textContent = "Signing in...";
      spinner.classList.remove("hidden");

      try {
        // Create form data as backend expects OAuth2 format
        const formData = new FormData();
        formData.append('username', form.username.value.trim());
        formData.append('password', form.password.value.trim());

        const response = await fetch("http://localhost:8000/login", {
          method: "POST",
          body: formData  // Let browser set Content-Type with boundary
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Login failed. Please check your credentials.");
        }

        // Success handling
        messageEl.textContent = "Login successful! Redirecting...";
        messageEl.classList.add("text-green-600");
        messageEl.classList.remove("hidden");
        
        // Store token and redirect
        localStorage.setItem("access_token", data.access_token);
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 1500);
        
      } catch (error) {
        console.error("Login error:", error);
        messageEl.textContent = error.message || "An error occurred. Please try again.";
        messageEl.classList.add("text-red-600");
        messageEl.classList.remove("hidden");
        
        // Re-enable button
        submitBtn.disabled = false;
        btnText.textContent = "Sign In";
        spinner.classList.add("hidden");
      }
    });
  


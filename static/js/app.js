document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("appSidebar");
  const sidebarBackdrop = document.getElementById("sidebarBackdrop");
  const menuToggle = document.querySelector(".menu-toggle");
  const sidebarClose = document.querySelector(".sidebar-close");

  const setSidebar = (open) => {
    if (!sidebar || !sidebarBackdrop) return;
    sidebar.classList.toggle("is-open", open);
    sidebarBackdrop.classList.toggle("is-visible", open);
    menuToggle?.setAttribute("aria-expanded", String(open));
  };

  menuToggle?.addEventListener("click", () => setSidebar(true));
  sidebarClose?.addEventListener("click", () => setSidebar(false));
  sidebarBackdrop?.addEventListener("click", () => setSidebar(false));
  sidebar?.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setSidebar(false)));

  const deleteModal = document.getElementById("deleteModal");
  const deleteForm = document.getElementById("deleteForm");
  const deleteTaskName = document.getElementById("deleteTaskName");
  if (deleteModal && deleteForm) {
    deleteModal.addEventListener("show.bs.modal", (event) => {
      const trigger = event.relatedTarget;
      deleteForm.action = trigger.dataset.deleteUrl;
      deleteTaskName.textContent = `“${trigger.dataset.taskName}”`;
    });
  }

  const createModal = document.getElementById("createModal");
  createModal?.addEventListener("shown.bs.modal", () => document.getElementById("new-task")?.focus());
});

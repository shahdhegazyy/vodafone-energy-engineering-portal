(() => {
  const guide = document.getElementById("usage-guide");
  if (!guide) return;
  const titles = {
    cable: ["How to use DC Cable Design", "Engineering cable selection across four conductor-temperature cases."],
    rack: ["How to use AC/DC Rack Design", "Build the rack, calculate its power demand and review its protection checks."],
    onsite: ["How to use On-Site Recommendation", "A short field workflow for technicians using fixed copper at 25°C."],
  };
  const open = key => {
    document.querySelectorAll("[data-demo]").forEach(demo => { demo.hidden = demo.dataset.demo !== key; });
    document.getElementById("guide-title").textContent = titles[key][0];
    document.getElementById("guide-subtitle").textContent = titles[key][1];
    guide.hidden = false;
    document.body.style.overflow = "hidden";
  };
  const close = () => { guide.hidden = true; document.body.style.overflow = ""; };
  document.querySelectorAll("[data-guide]").forEach(button => button.addEventListener("click", () => open(button.dataset.guide)));
  document.querySelectorAll("[data-close-guide]").forEach(button => button.addEventListener("click", close));
  guide.addEventListener("click", event => { if (event.target === guide) close(); });
  document.addEventListener("keydown", event => { if (event.key === "Escape" && !guide.hidden) close(); });
})();

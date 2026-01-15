export default class Modal extends HTMLElement {
    #restoreData = "";

    connectedCallback() {
        const restore = this.querySelector('[data-restore-on-close="true"]');
        if (restore) {
            this.#restoreData = this.innerHTML;
        }
        const closeBtns = this.querySelectorAll('button[data-action="close"]');
        for (const close of closeBtns) {
            close.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
    
                this.hide();
            });
        }
        this.addEventListener('close-modal', () => {
            this.hide();
        })

        const eles = this.querySelectorAll('[data-modal-on-outside-click="true"]');
        this.addEventListener("click", (e) => {
            if (e.target !== this) {
                return;
            }
            for (const el of eles) {
                if (el.modalOutsideClicked) {
                    el.modalOutsideClicked();
                }
            }
        });
    }

    hide() {
        if (this.#restoreData !== "") {
            this.innerHTML = this.#restoreData;
            this.connectedCallback();
        }
        this.classList.add("hidden");
    }

    show(...args) {
        const eles = this.querySelectorAll('[data-modal-show="true"]');
        for (const ele of eles) {
            if (ele.show) {
                ele.show(...args)
            }
        }
        this.classList.remove("hidden");
    }
}

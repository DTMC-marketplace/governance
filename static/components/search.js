import Tagify from 'tagify';

function tagTemplate(tagData) {
    return `<tag title='${tagData.value}' contenteditable='false' spellcheck="false" class='tagify__tag ${tagData.class ? tagData.class : ""}' ${this.getAttributes(tagData)}>
                <x title='remove tag' class='tagify__tag__removeBtn'></x>
                <div>
                    <span class='tagify__tag-text tag-${tagData.class}'>${tagData.value}</span>
                </div>
            </tag>`
}

function dropdownItem(tagData) {
    return `
        <div ${this.getAttributes(tagData)}
            class='tagify__dropdown__item tag-${tagData.class ? tagData.class : ""}'
            tabindex="0"
            role="option">
            <span>${tagData.value}</span>
        </div>
    `
}

export default class Search extends HTMLElement {
    #controller;
    #rootUrl = "/Overview/";
    #searchUrl = "/search/suggestions/";

    #onChange(e) {
        let url = "";
        const tagify = e.detail.tagify;
        const tags = e.detail.tagify.getCleanValue();
        const companyId = this.getAttribute('company-id');
        const platform = this.getAttribute('data-platform');

        for (const tag of tags) {
            if (tag.class == "company") {
                tagify.off('change');
                tagify.removeAllTags();
                setTimeout(() => {
                    tagify.on('change', (e) => this.#onChange(e));
                }, 50000);
                //loads the company resulting from the search in read mode
                document.location.href =  `/${platform}/dashboard/${companyId}/companies/${tag.id}` + this.#rootUrl
                return; 
            }
            url += "/" + (tag.class ?? "all") + "/" + tag.value;
        }
    
        document.location.href =  `/${platform}/dashboard/${companyId}` + "/search/query" + url;                  
    }

    #onInput(e) {
        const tagify = e.detail.tagify;
        var value = e.detail.value;
        tagify.whitelist = null;
    
        this.#controller && this.#controller.abort();
        this.#controller = new AbortController();
    
        tagify.loading(true);
        fetch(this.#searchUrl + value, { signal: this.#controller.signal })
            .then(RES => RES.json())
            .then(function (newWhitelist) {
                tagify.whitelist = newWhitelist; // update whitelist Array in-place
                tagify.loading(false).dropdown.show(value); // render the suggestions dropdown
            }
        );
    }

    connectedCallback() {
        const searchUrl = this.getAttribute('search-url');
        const rootUrl = this.getAttribute('root-url');
        const multiSearch = this.getAttribute('multi-search');
        if (searchUrl) {
            this.#searchUrl = searchUrl;
        }
        if (rootUrl) {
            this.#rootUrl = rootUrl;
        }
        const input = this.querySelector('input[data-search="true"]');
        if (!input) {
            console.error("couldn't find input in search tags-search");
            return;
        }
        const templates = {
            tag: tagTemplate
        };
        if (multiSearch) {
            templates.dropdownItem = dropdownItem;
        }

        const tagify = new Tagify(input, {
            templates,
            whitelist: []
        });
        tagify.on('input', (e) => this.#onInput(e));
        tagify.on('change', (e) => this.#onChange(e));
    }
}

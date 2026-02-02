// Utility for notifications
function showNotification(message, type = 'info') {
    // For now use alert, but could be replaced with a toast UI
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Optional: could add a simple toast div if needed
    alert(message);
}

// Tab switching
// Tab switching
function switchTab(tabName, skipUpdate = false) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active', 'text-[#F13D30]', 'border-[#F13D30]');
        btn.classList.add('text-[#6B7280]', 'border-transparent');
    });
    
    // Show selected tab content
    document.getElementById('content-' + tabName).classList.remove('hidden');
    
    // Add active class to selected tab
    const activeTab = document.getElementById('tab-' + tabName);
    if (activeTab) {
        activeTab.classList.add('active', 'text-[#F13D30]', 'border-[#F13D30]');
        activeTab.classList.remove('text-[#6B7280]', 'border-transparent');
    }
    
    // Update assessment blocks when switching to Assessment tab
    if (tabName === 'assessment' && !skipUpdate) {
        // Use setTimeout to ensure tab switch happens first, then update blocks
        setTimeout(function() {
            try {
                if (typeof updateAllAssessmentBlocks === 'function') {
                    updateAllAssessmentBlocks();
                }
            } catch (error) {
                console.error('Error updating assessment blocks:', error);
            }
        }, 0);
    }
    
    // Update result blocks when switching to Result tab
    if (tabName === 'result') {
        // Use setTimeout to ensure tab switch happens first, then update blocks
        setTimeout(function() {
            try {
                if (typeof updateAllResultBlocks === 'function') {
                    updateAllResultBlocks();
                }
            } catch (error) {
                console.error('Error updating result blocks:', error);
            }
        }, 0);
    }
}

// Save section data (saves all profile data)
async function saveSection() {
    // Ensure vendor link is saved to the saved div if it exists in input but not in saved div
    const linkInput = document.getElementById('vendor-evidence-link');
    const savedLinkDiv = document.getElementById('vendor-link-saved');
    const linkText = document.getElementById('vendor-link-text');
    
    if (linkInput && linkInput.value && linkInput.value.trim()) {
        // If input has value but saved div is hidden, update saved div
        if (savedLinkDiv && savedLinkDiv.classList.contains('hidden')) {
            if (linkText) {
                linkText.innerHTML = `<a href="${linkInput.value.trim()}" target="_blank" class="text-[#F13D30] hover:underline">${linkInput.value.trim()}</a>`;
                savedLinkDiv.classList.remove('hidden');
            }
        }
    }
    
    // Save all profile data (sections are part of profile)
    const success = await saveProfileData();
    if (success) {
        alert('Section saved successfully!');
    } else {
        alert('Error saving section. Please try again.');
    }
}

// Save all and proceed to Assessment
async function saveAllAndProceedToAssessment() {
    // Save all profile data first
    const success = await saveProfileData();
    if (success) {
        // Switch to Assessment tab, but SKIP triggering updateAllAssessmentBlocks 
        // because saveProfileData already called updateAssessmentBlocksFromBE with fresh data.
        
        // RESET session confirmation to force confirmation prompt on new profile data
        block2State.uiConfirmedInSession = false;
        
        switchTab('assessment', true);
    } else {
        alert('Error saving data. Please try again.');
    }
}

// Proceed to Result
function proceedToResult() {
    try {
        // Recheck and update all result blocks before switching
        if (typeof updateAllResultBlocks === 'function') {
            updateAllResultBlocks();
        }
    } catch (error) {
        console.error('Error updating result blocks:', error);
    }
    // Switch to Result tab
    switchTab('result');
}

// Section toggle
function toggleSection(sectionId) {
    const content = document.getElementById(sectionId + '-content');
    const toggle = document.getElementById(sectionId + '-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.src = '{% static "governance/img/chevron-up.svg" %}';
    } else {
        content.style.display = 'none';
        toggle.src = '{% static "governance/img/chevron-down.svg" %}';
    }
}

// Load AI System detail data from API
async function loadAISystemDetailData() {
    // Get agent_id from data attribute
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    if (!agentId) {
        console.warn('No agent ID available');
        return;
    }
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/detail/`, {
            method: 'GET',
        });
        
        const result = await response.json();
        
        if (result.success && result.data) {
            // Load documents
            if (result.data.documents && result.data.documents.length > 0) {
                loadDocuments(result.data.documents);
            }
            
            // Load profile data if exists
            if (result.data.profile) {
                loadProfileData(result.data.profile);
            }
            
            // Load assessment data if exists
            if (result.data.assessment) {
                loadAssessmentData(result.data.assessment);
                
                if (result.data.assessment.block1) {
                    block1State.be_assessment = result.data.assessment.block1;
                }
                if (result.data.assessment.block1_state) {
                    const b1s = result.data.assessment.block1_state;
                    block1State.prohibitedConfirmed = b1s.prohibited_confirmed || false;
                    block1State.claimingException = b1s.claiming_exception || '';
                    block1State.exceptionQualifies = b1s.exception_qualifies || '';
                    block1State.exceptionEvidenceUploaded = b1s.exception_evidence_uploaded || false;
                    block1State.exceptionEvidenceSavedLink = b1s.exception_evidence_saved_link || '';
                    block1State.noExceptionConfirmed = b1s.no_exception_confirmed || false;
                }
                
                if (result.data.assessment.block2) {
                    block2State.be_assessment = result.data.assessment.block2;
                }
                if (result.data.assessment.block2_state) {
                    const b2s = result.data.assessment.block2_state;
                    block2State.highRiskConfirmed = b2s.high_risk_confirmed || false;
                    block2State.materialInfluence = b2s.material_influence || '';
                    block2State.narrowTasks = b2s.narrow_tasks || [];
                    block2State.profiling = b2s.profiling || '';
                    block2State.exemptionEvidenceUploaded = b2s.exemption_evidence_uploaded || false;
                    block2State.exemptionEvidenceSavedLink = b2s.exemption_evidence_saved_link || '';
                }
                
                if (result.data.assessment.block3) {
                    block3State.be_assessment = result.data.assessment.block3;
                }
                if (result.data.assessment.block3_state) {
                    const b3s = result.data.assessment.block3_state;
                    block3State.transparencyConfirmed = b3s.transparency_confirmed || false;
                    block3State.exceptionOptions = b3s.exception_options || [];
                    block3State.transparencyEvidenceUploaded = b3s.transparency_evidence_uploaded || false;
                    block3State.transparencyEvidenceSavedLink = b3s.transparency_evidence_saved_link || '';
                }
                
                if (result.data.assessment.block4) {
                    block4State.be_assessment = result.data.assessment.block4;
                }
                if (result.data.assessment.block4_state) {
                    const b4s = result.data.assessment.block4_state;
                    block4State.gpaiConfirmed = b4s.gpai_confirmed || false;
                    block4State.gpaiProviderAnswer = b4s.gpai_provider_answer || '';
                }
            }
            
            console.log('AI System detail data loaded successfully');
        } else {
            console.log('No saved detail data found, starting fresh');
        }
    } catch (error) {
        console.error('Error loading AI System detail data:', error);
    }
}

// Load documents into UI
function loadDocuments(documents) {
    const container = document.getElementById('uploaded-documents');
    if (!container) return;
    
    container.innerHTML = ''; // Clear existing
    
    documents.forEach((doc, index) => {
        const fileId = 'file-' + Date.now() + '-' + index;
        const fileItem = document.createElement('div');
        fileItem.className = 'flex items-center justify-between p-3 bg-white rounded-lg border border-[#E5E7EB]';
        fileItem.setAttribute('data-file-name', doc.name || '');
        fileItem.setAttribute('data-file-url', doc.url || '');
        fileItem.setAttribute('data-file-path', doc.path || '');
        
        // Calculate time ago
        let uploadedText = 'recently';
        if (doc.uploaded_at) {
            try {
                const uploadedDate = new Date(doc.uploaded_at);
                const now = new Date();
                const diffMs = now - uploadedDate;
                const diffMins = Math.floor(diffMs / 60000);
                
                if (diffMins < 1) {
                    uploadedText = 'just now';
                } else if (diffMins < 60) {
                    uploadedText = `${diffMins} mins ago`;
                } else if (diffMins < 1440) {
                    uploadedText = `${Math.floor(diffMins / 60)} hours ago`;
                } else {
                    uploadedText = `${Math.floor(diffMins / 1440)} days ago`;
                }
            } catch (e) {
                uploadedText = 'recently';
            }
        }
        
        fileItem.innerHTML = `
            <div class="flex items-center gap-3">
                <label class="cursor-pointer">
                    <input type="checkbox" class="file-checkbox hidden" data-file-id="${fileId}" onchange="toggleFileSelection(this)">
                    <div class="file-checkbox-display w-5 h-5 border-2 border-[#111827] rounded flex items-center justify-center">
                        <svg class="hidden check-icon w-3 h-3 text-[#F13D30]" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                        </svg>
                    </div>
                </label>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    class="w-5 h-5 text-[#DC2626]">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14,2 14,8 20,8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                    <polyline points="10,9 9,9 8,9" />
                </svg>
                <div>
                    <p class="text-sm font-medium text-[#111827]">${doc.name || 'Unknown'}</p>
                    <p class="text-xs text-[#6B7280]">Uploaded ${uploadedText}</p>
                </div>
            </div>
            <button onclick="generateLink('${doc.name || ''}')" class="flex items-center gap-2 px-4 py-1.5 bg-[#F13D30] text-white text-sm rounded-lg hover:bg-[#d63529] transition-colors">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                </svg>
                Generate link
            </button>
        `;
        container.appendChild(fileItem);
    });
    
    updateDeleteButtonVisibility();
}

// Load profile data into form fields
function loadProfileData(profileData) {
    if (!profileData) return;
    
    console.log('Loading profile data:', profileData);
    
    // Section 2: System Identity
    if (profileData.system_identity) {
        const si = profileData.system_identity;
        setValue('ai_system_name', si.ai_system_name);
        setValue('internal_system_id', si.internal_system_id);
        setValue('commercial_name', si.commercial_name);
        setValue('owner_name', si.owner_name);
        setValue('owner_email', si.owner_email);
        setValue('owner_department', si.owner_department);
        setChecked('same_as_compliance_owner', si.same_as_compliance_owner);
        setValue('system_status', si.system_status);
        setValue('go_live_date', si.go_live_date);
        setRadio('part_of_product', si.part_of_product);
        setValue('product_service_name', si.product_service_name);
    }
    
    // Section 3: Source & Operator Role
    if (profileData.source_operator_role) {
        const sor = profileData.source_operator_role;
        setRadio('default_role_apply', sor.default_role_apply);
        setCheckboxes('roles[]', sor.roles);  // Fix: field name is roles[]
        setRadio('system_source', sor.system_source);
        setValue('vendor_name', sor.vendor_name);
        setVendorEvidenceLink(sor.vendor_evidence_link);  // Set link to saved div
        setRadio('modify_customize', sor.modify_customize);
        setRadio('eu_usage', sor.eu_usage);
        setRadio('eu_effect', sor.eu_effect);
        if (window.refreshEuActNotice) window.refreshEuActNotice();
    }
    
    // Section 4: Intended Purpose
    if (profileData.intended_purpose) {
        const ip = profileData.intended_purpose;
        setValue('intended_purpose', ip.intended_purpose);
        setCheckboxes('sector_domain', ip.sector_domain);
        setValue('sector_other', ip.sector_other);
        setRadio('safety_component', ip.safety_component);
        setRadio('third_party_conformity', ip.third_party_conformity);
    }
    
    // Section 5-9: Other sections
    if (profileData.deployment_context) {
        setRadio('deployment_context', profileData.deployment_context);  // Fix: deployment_context is radio
        // Show Other input if value is "Other"
        if (profileData.deployment_context === 'Other' && profileData.deployment_other) {
            setTimeout(() => {
                const otherInput = document.getElementById('deployment-other-input');
                if (otherInput) {
                    otherInput.classList.remove('hidden');
                    otherInput.value = profileData.deployment_other;
                }
            }, 100);
        }
    }
    if (profileData.system_users) {
        setCheckboxes('system_users', profileData.system_users);
        // Show Other input if "Other" is selected
        if (profileData.system_users.includes('Other') && profileData.system_users_other) {
            setTimeout(() => {
                const otherInput = document.getElementById('system-users-other-input');
                if (otherInput) {
                    otherInput.classList.remove('hidden');
                    otherInput.value = profileData.system_users_other;
                }
            }, 100);
        }
    }
    if (profileData.affected_outputs) {
        setCheckboxes('affected_outputs', profileData.affected_outputs);
        // Show Other input if "Other" is selected
        if (profileData.affected_outputs.includes('Other') && profileData.affected_outputs_other) {
            setTimeout(() => {
                const otherInput = document.getElementById('affected-outputs-other-input');
                if (otherInput) {
                    otherInput.classList.remove('hidden');
                    otherInput.value = profileData.affected_outputs_other;
                }
            }, 100);
        }
    }
    if (profileData.vulnerable_groups) setCheckboxes('vulnerable_groups', profileData.vulnerable_groups);
    if (profileData.workflow_role) setRadio('workflow_role', profileData.workflow_role);
    if (profileData.output_types) setCheckboxes('output_types', profileData.output_types);
    if (profileData.decision_influence) setRadio('decision_influence', profileData.decision_influence);
    if (profileData.auto_execute) setRadio('auto_execute', profileData.auto_execute);
    if (profileData.capability_practices) setCheckboxes('capability_practices', profileData.capability_practices);
    if (profileData.interacts_persons) setRadio('interacts_persons', profileData.interacts_persons);
    if (profileData.synthetic_content) setCheckboxes('synthetic_content', profileData.synthetic_content);
    if (profileData.ai_kind) setCheckboxes('ai_kind', profileData.ai_kind);
    if (profileData.gpai_integration) setRadio('gpai_integration', profileData.gpai_integration);
    if (profileData.gpai_provider) setValue('gpai_provider', profileData.gpai_provider);
    if (profileData.training_source) setRadio('training_source', profileData.training_source);
    if (profileData.update_frequency) setRadio('update_frequency', profileData.update_frequency);
    if (profileData.data_types) setCheckboxes('data_types', profileData.data_types);
}

// Helper functions to set form values
function setValue(name, value) {
    if (!value) return;
    const field = document.querySelector(`[name="${name}"]`);
    if (field) {
        if (field.type === 'checkbox') {
            field.checked = value;
        } else {
            field.value = value;
        }
    }
}

function setRadio(name, value) {
    if (!value) return;
    const radio = document.querySelector(`[name="${name}"][value="${value}"]`);
    if (radio) {
        radio.checked = true;
        // Trigger change event for conditional logic (important for system_source to show vendor fields, safety_component to show third_party_conformity)
        radio.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Special handling for system_source to ensure vendor fields are shown
        if (name === 'system_source' && (value === 'Vendor / Third-party' || value === 'Mixed')) {
            setTimeout(() => {
                const vendorFields = document.getElementById('vendor-fields');
                if (vendorFields) {
                    vendorFields.classList.remove('hidden');
                }
            }, 100);
        }
        
        // Special handling for safety_component to ensure third_party_conformity field is shown
        if (name === 'safety_component' && value === 'Yes') {
            setTimeout(() => {
                const thirdPartyField = document.getElementById('third-party-conformity-field');
                if (thirdPartyField) {
                    thirdPartyField.classList.remove('hidden');
                }
            }, 100);
        }
    }
}

function setCheckboxes(name, values) {
    if (!values || !Array.isArray(values)) {
        // If no values, uncheck all checkboxes with this name
        const allCheckboxes = document.querySelectorAll(`[name="${name}"], [name="${name}[]"]`);
        allCheckboxes.forEach(cb => cb.checked = false);
        return;
    }
    
    // First, uncheck all checkboxes with this name
    const allCheckboxes = document.querySelectorAll(`[name="${name}"], [name="${name}[]"]`);
    allCheckboxes.forEach(cb => cb.checked = false);
    
    // Then, check only the ones in the values array
    values.forEach(value => {
        // Support both "roles" and "roles[]" format
        const checkbox = document.querySelector(`[name="${name}"][value="${value}"], [name="${name}[]"][value="${value}"]`);
        if (checkbox) {
            checkbox.checked = true;
        }
    });
}

// Set vendor evidence link to saved div
function setVendorEvidenceLink(link) {
    if (!link) return;
    
    const savedLinkDiv = document.getElementById('vendor-link-saved');
    const linkText = document.getElementById('vendor-link-text');
    const linkInput = document.getElementById('vendor-evidence-link');
    
    if (savedLinkDiv && linkText) {
        // Create clickable link
        linkText.innerHTML = `<a href="${link}" target="_blank" class="text-[#F13D30] hover:underline">${link}</a>`;
        savedLinkDiv.classList.remove('hidden');
        
        // Also set input value for reference
        if (linkInput) {
            linkInput.value = link;
        }
    } else if (linkInput) {
        // Fallback to input field
        linkInput.value = link;
    }
}

function setChecked(name, checked) {
    if (checked === undefined || checked === null) return;
    const checkbox = document.getElementById(name) || document.querySelector(`[name="${name}"]`);
    if (checkbox) {
        checkbox.checked = checked;
        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

// Collect all profile form data
function collectProfileData() {
    // Debug: Check vendor evidence link before collecting
    const vendorLink = getVendorEvidenceLink();
    console.log('Collecting profile data - vendor_evidence_link:', vendorLink);
    
    const profile = {
        system_identity: {
            ai_system_name: getValue('ai_system_name'),
            internal_system_id: getValue('internal_system_id'),
            commercial_name: getValue('commercial_name'),
            owner_name: getValue('owner_name'),
            owner_email: getValue('owner_email'),
            owner_department: getValue('owner_department'),
            same_as_compliance_owner: getChecked('same_as_compliance_owner'),
            system_status: getValue('system_status'),
            go_live_date: getValue('go_live_date'),
            part_of_product: getRadio('part_of_product'),
            product_service_name: getValue('product_service_name')
        },
        source_operator_role: {
            default_role_apply: getRadio('default_role_apply'),
            roles: getCheckboxes('roles[]'),  // Fix: field name is roles[]
            system_source: getRadio('system_source'),
            vendor_name: getValue('vendor_name'),
            vendor_evidence_link: getVendorEvidenceLink(),  // Get link from saved div or input
            modify_customize: getRadio('modify_customize'),
            eu_usage: getRadio('eu_usage'),
            eu_effect: getRadio('eu_effect')
        },
        intended_purpose: {
            intended_purpose: getValue('intended_purpose'),
            sector_domain: getCheckboxes('sector_domain'),
            sector_other: getValue('sector_other'),
            safety_component: getRadio('safety_component'),
            third_party_conformity: getRadio('third_party_conformity')
        },
        deployment_context: getRadio('deployment_context'),  // Fix: deployment_context is radio, not checkbox
        deployment_other: getValue('deployment_other'),  // Add Other field
        system_users: getCheckboxes('system_users'),
        system_users_other: getValue('system_users_other'),  // Add Other field
        affected_outputs: getCheckboxes('affected_outputs'),
        affected_outputs_other: getValue('affected_outputs_other'),  // Add Other field
        vulnerable_groups: getCheckboxes('vulnerable_groups'),
        workflow_role: getRadio('workflow_role'),
        output_types: getCheckboxes('output_types'),
        decision_influence: getRadio('decision_influence'),
        auto_execute: getRadio('auto_execute'),
        capability_practices: getCheckboxes('capability_practices'),
        interacts_persons: getRadio('interacts_persons'),
        synthetic_content: getCheckboxes('synthetic_content'),
        ai_kind: getCheckboxes('ai_kind'),
        gpai_integration: getRadio('gpai_integration'),
        gpai_provider: getValue('gpai_provider'),
        training_source: getRadio('training_source'),
        update_frequency: getRadio('update_frequency'),
        data_types: getCheckboxes('data_types')
    };
    
    return profile;
}

// Helper functions to get form values
function getValue(name) {
    const field = document.querySelector(`[name="${name}"]`);
    return field ? field.value : '';
}

function getRadio(name) {
    const radio = document.querySelector(`[name="${name}"]:checked`);
    return radio ? radio.value : '';
}

function getCheckboxes(name) {
    // Support both "roles" and "roles[]" format
    // IMPORTANT: Only get checked checkboxes, not all checkboxes
    const checkboxes = Array.from(document.querySelectorAll(`[name="${name}"]:checked, [name="${name}[]"]:checked`));
    return checkboxes.map(cb => cb.value);
}

// Get vendor evidence link from saved div or input field
function getVendorEvidenceLink() {
    const savedLinkDiv = document.getElementById('vendor-link-saved');
    const linkText = document.getElementById('vendor-link-text');
    const linkInput = document.getElementById('vendor-evidence-link');
    
    // Debug
    console.log('getVendorEvidenceLink - savedLinkDiv:', savedLinkDiv);
    console.log('getVendorEvidenceLink - linkText:', linkText);
    console.log('getVendorEvidenceLink - linkInput:', linkInput);
    console.log('getVendorEvidenceLink - linkInput.value:', linkInput?.value);
    
    // Priority: Check input field first (most up-to-date)
    // Then check saved div
    if (linkInput && linkInput.value && linkInput.value.trim()) {
        const linkValue = linkInput.value.trim();
        console.log('getVendorEvidenceLink - returning from input:', linkValue);
        return linkValue;
    }
    
    // Fallback to saved div if input is empty
    if (savedLinkDiv && !savedLinkDiv.classList.contains('hidden') && linkText) {
        // Extract link from text or href if it's a link element
        const linkMatch = linkText.innerHTML.match(/href="([^"]+)"/);
        if (linkMatch) {
            console.log('getVendorEvidenceLink - returning from saved div (href):', linkMatch[1]);
            return linkMatch[1];
        }
        // Or get text content if it's just text
        const text = linkText.textContent || linkText.innerText;
        if (text && text.trim()) {
            console.log('getVendorEvidenceLink - returning from saved div (text):', text.trim());
            return text.trim();
        }
    }
    
    console.log('getVendorEvidenceLink - returning empty string');
    return '';
}

function getChecked(name) {
    const checkbox = document.getElementById(name) || document.querySelector(`[name="${name}"]`);
    return checkbox ? checkbox.checked : false;
}

// Save profile data to API
async function saveProfileData() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    if (!agentId) {
        console.error('No agent ID available');
        return false;
    }
    
    try {
        // Ensure vendor link is captured from input field if user hasn't clicked "Save link"
        const linkInput = document.getElementById('vendor-evidence-link');
        if (linkInput && linkInput.value && linkInput.value.trim()) {
            // Update saved div to reflect current input value
            const savedLinkDiv = document.getElementById('vendor-link-saved');
            const linkText = document.getElementById('vendor-link-text');
            if (savedLinkDiv && linkText) {
                linkText.innerHTML = `<a href="${linkInput.value.trim()}" target="_blank" class="text-[#F13D30] hover:underline">${linkInput.value.trim()}</a>`;
                savedLinkDiv.classList.remove('hidden');
            }
        }
        
        const profileData = collectProfileData();
        console.log('Saving profile data:', profileData);
        console.log('Vendor evidence link in profile:', profileData.source_operator_role?.vendor_evidence_link);
        
        const response = await fetch(`/api/ai-inventory/${agentId}/detail/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                profile: profileData
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Profile data saved successfully');
            
            // If assessment results are returned from BE, update assessment blocks
            if (result.assessment) {
                console.log('Assessment results from BE:', result.assessment);
                updateAssessmentBlocksFromBE(result.assessment);
            }
            
            return true;
        } else {
            console.error('Error saving profile data:', result.error);
            return false;
        }
    } catch (error) {
        console.error('Error saving profile data:', error);
        return false;
    }
}

// Load assessment data (placeholder - to be implemented based on form structure)
function loadAssessmentData(assessmentData) {
    if (!assessmentData) return;
    console.log('Loading assessment data:', assessmentData);
    // TODO: Implement loading assessment form fields when needed
}

// File upload handling
document.getElementById('file-upload')?.addEventListener('change', async function(e) {
    const files = Array.from(e.target.files);
    const container = document.getElementById('uploaded-documents');
    if (!container || !files?.length) return;
    
    // Get agent_id from data attribute
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    // Upload files to static folder using general upload API
    try {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('file', file);
        });
        formData.append('folder', 'governance/uploads');
        
        const uploadResponse = await fetch('/api/upload-file/', {
            method: 'POST',
            body: formData,
        });
        
        const uploadResult = await uploadResponse.json();
        
        if (!uploadResponse.ok || !uploadResult.success) {
            throw new Error(uploadResult.error || uploadResult.message || 'Upload failed');
        }
        
        // Prepare file info
        const fileInfos = uploadResult.files.map(fileInfo => ({
            name: fileInfo.name,
            size: fileInfo.size,
            url: fileInfo.url,
            path: fileInfo.path,
            uploaded_at: new Date().toISOString()
        }));
        
        // Get existing documents
        let existingDocuments = [];
        try {
            const getResponse = await fetch(`/api/ai-inventory/${agentId}/detail/`);
            const getResult = await getResponse.json();
            if (getResult.success && getResult.data && getResult.data.documents) {
                existingDocuments = getResult.data.documents;
            }
        } catch (e) {
            console.warn('Could not load existing documents:', e);
        }
        
        // Merge new files with existing
        const allDocuments = [...existingDocuments, ...fileInfos];
        
        // Save documents to detail API
        try {
            const saveResponse = await fetch(`/api/ai-inventory/${agentId}/detail/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    documents: allDocuments
                })
            });
            
            if (!saveResponse.ok) {
                console.warn('Could not save file info to detail data');
            }
        } catch (e) {
            console.warn('Error saving file info:', e);
        }
        
        // Add uploaded files to UI
        fileInfos.forEach(fileInfo => {
            const fileId = 'file-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            const fileItem = document.createElement('div');
            fileItem.className = 'flex items-center justify-between p-3 bg-white rounded-lg border border-[#E5E7EB]';
            fileItem.setAttribute('data-file-name', fileInfo.name);
            fileItem.setAttribute('data-file-url', fileInfo.url);
            fileItem.setAttribute('data-file-path', fileInfo.path);
            fileItem.innerHTML = `
                <div class="flex items-center gap-3">
                    <label class="cursor-pointer">
                        <input type="checkbox" class="file-checkbox hidden" data-file-id="${fileId}" onchange="toggleFileSelection(this)">
                        <div class="file-checkbox-display w-5 h-5 border-2 border-[#111827] rounded flex items-center justify-center">
                            <svg class="hidden check-icon w-3 h-3 text-[#F13D30]" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                        </div>
                    </label>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        class="w-5 h-5 text-[#DC2626]">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14,2 14,8 20,8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                        <polyline points="10,9 9,9 8,9" />
                    </svg>
                    <div>
                        <p class="text-sm font-medium text-[#111827]">${fileInfo.name}</p>
                        <p class="text-xs text-[#6B7280]">Uploaded just now</p>
                    </div>
                </div>
                <button onclick="generateLink('${fileInfo.name}')" class="flex items-center gap-2 px-4 py-1.5 bg-[#F13D30] text-white text-sm rounded-lg hover:bg-[#d63529] transition-colors">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                    Generate link
                </button>
            `;
            container.appendChild(fileItem);
        });
        
        e.target.value = '';
        updateDeleteButtonVisibility();
    } catch (error) {
        console.error('Upload error:', error);
        alert(`Error uploading files: ${error.message}`);
    }
});

// Toggle file selection
function toggleFileSelection(checkbox) {
    const display = checkbox.nextElementSibling;
    const checkIcon = display.querySelector('.check-icon');
    
    if (checkbox.checked) {
        display.classList.remove('border-[#111827]');
        display.classList.add('border-[#F13D30]', 'bg-white');
        checkIcon.classList.remove('hidden');
    } else {
        display.classList.remove('border-[#F13D30]');
        display.classList.add('border-[#111827]');
        checkIcon.classList.add('hidden');
    }
    
    // Update delete button visibility
    updateDeleteButtonVisibility();
}

// Update delete button visibility based on selected files
function updateDeleteButtonVisibility() {
    const selectedCheckboxes = document.querySelectorAll('.file-checkbox:checked');
    const deleteBtn = document.getElementById('delete-selected-files-btn');
    
    if (deleteBtn) {
        if (selectedCheckboxes.length > 0) {
            deleteBtn.classList.remove('hidden');
        } else {
            deleteBtn.classList.add('hidden');
        }
    }
}

// Delete selected files
async function deleteSelectedFiles() {
    const selectedCheckboxes = document.querySelectorAll('.file-checkbox:checked');
    
    if (selectedCheckboxes.length === 0) {
        return;
    }
    
    const confirmDelete = confirm(
        `Are you sure you want to delete ${selectedCheckboxes.length} selected file${selectedCheckboxes.length > 1 ? 's' : ''}? This action cannot be undone.`
    );
    
    if (!confirmDelete) {
        return;
    }
    
    // Get agent_id
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    // Collect file information from selected checkboxes
    const filesToDelete = [];
    selectedCheckboxes.forEach(checkbox => {
        const fileItem = checkbox.closest('.flex.items-center.justify-between');
        if (fileItem) {
            const fileName = fileItem.getAttribute('data-file-name');
            const fileUrl = fileItem.getAttribute('data-file-url');
            const filePath = fileItem.getAttribute('data-file-path');
            
            if (fileName) {
                filesToDelete.push({
                    name: fileName,
                    url: fileUrl || '',
                    path: filePath || ''
                });
            }
        }
    });
    
    if (filesToDelete.length === 0) {
        alert('No file information found to delete');
        return;
    }
    
    try {
        // Get current documents
        let currentDocuments = [];
        try {
            const getResponse = await fetch(`/api/ai-inventory/${agentId}/detail/`);
            const getResult = await getResponse.json();
            if (getResult.success && getResult.data && getResult.data.documents) {
                currentDocuments = getResult.data.documents;
            }
        } catch (e) {
            console.warn('Could not load current documents:', e);
        }
        
        // Remove deleted files from documents array
        const remainingDocuments = currentDocuments.filter(doc => {
            return !filesToDelete.some(fileToDelete => fileToDelete.name === doc.name);
        });
        
        // Update detail data
        const saveResponse = await fetch(`/api/ai-inventory/${agentId}/detail/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                documents: remainingDocuments
            })
        });
        
        if (!saveResponse.ok) {
            throw new Error('Failed to update documents');
        }
        
        // Remove file items from DOM
        selectedCheckboxes.forEach(checkbox => {
            const fileItem = checkbox.closest('.flex.items-center.justify-between');
            if (fileItem) {
                fileItem.remove();
            }
        });
        
        // Update delete button visibility after deletion
        updateDeleteButtonVisibility();
        
        console.log(`Successfully deleted ${filesToDelete.length} file(s)`);
    } catch (error) {
        console.error('Error deleting files:', error);
        alert(`Error deleting files: ${error.message}`);
    }
}

// Initialize delete button visibility on page load
document.addEventListener('DOMContentLoaded', function() {
    updateDeleteButtonVisibility();
});

// AI Read toggle
document.querySelectorAll('.ai-read-toggle').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.ai-read-toggle').forEach(b => {
            b.classList.remove('active');
            b.classList.remove('bg-[#F13D30]', 'text-white', 'shadow-sm');
            b.classList.add('border', 'border-[#F13D30]', 'text-[#F13D30]', 'bg-white');
            // Update icon to red
            const icon = b.querySelector('img');
            if (icon) {
                icon.style.filter = 'brightness(0) saturate(100%) invert(32%) sepia(98%) saturate(1500%) hue-rotate(344deg) brightness(98%) contrast(95%)';
            }
        });
        this.classList.add('active', 'bg-[#F13D30]', 'text-white', 'shadow-sm');
        this.classList.remove('border', 'border-[#F13D30]', 'text-[#F13D30]', 'bg-white');
        // Update icon to white
        const icon = this.querySelector('img');
        if (icon) {
            icon.style.filter = 'brightness(0) invert(1)';
        }
    });
});

// Generate link function
function generateLink(fileName) {
    const safeName = fileName || 'document';
    const randomId = (self.crypto && self.crypto.randomUUID) ? self.crypto.randomUUID() : Date.now().toString(36);
    const link = `https://${randomId}`;
    openShareModal(safeName, link);
}

// Generate link modal helpers
function openShareModal(fileName, link) {
    const modal = document.getElementById('share-link-modal');
    const nameEl = document.getElementById('share-file-name');
    const inputEl = document.getElementById('share-link-input');
    const copyBtn = document.getElementById('share-link-copy-btn');
    if (!modal || !nameEl || !inputEl || !copyBtn) return;

    nameEl.textContent = fileName;
    inputEl.value = link;
    modal.classList.remove('hidden');

    // Reset button to initial state
    const iconEl = document.getElementById('share-link-chain-icon');
    const textEl = document.getElementById('share-link-text');
    if (iconEl && textEl) {
        // Reset to chain-link icon
        iconEl.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>';
        textEl.textContent = 'Copy';
    }
}

function closeShareModal() {
    const modal = document.getElementById('share-link-modal');
    if (modal) modal.classList.add('hidden');
}

// Copy button handler
document.getElementById('share-link-copy-btn')?.addEventListener('click', function() {
    const inputEl = document.getElementById('share-link-input');
    const iconEl = document.getElementById('share-link-chain-icon');
    const textEl = document.getElementById('share-link-text');
    
    if (!inputEl || !inputEl.value || !iconEl || !textEl) return;
    
    navigator.clipboard.writeText(inputEl.value).then(() => {
        // Change icon to checkmark
        iconEl.innerHTML = '<polyline points="20,6 9,17 4,12" stroke-linecap="round" stroke-linejoin="round" stroke-width="3"></polyline>';
        // Change text to "Copied"
        textEl.textContent = 'Copied';
    }).catch(() => {
        alert('Unable to copy link');
    });
});

// Close modal when clicking outside content
document.getElementById('share-link-modal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeShareModal();
    }
});

// Assessment Block Logic
let assessmentBlockStates = {
    1: false, 2: false, 3: false, 4: false
};

function toggleAssessmentBlock(blockNum) {
    const content = document.getElementById(`block-${blockNum}-content`);
    const chevron = document.getElementById(`block-${blockNum}-chevron`);
    
    if (assessmentBlockStates[blockNum]) {
        content.classList.add('hidden');
        chevron.src = '{% static "governance/img/chevron-down.svg" %}';
        assessmentBlockStates[blockNum] = false;
    } else {
        content.classList.remove('hidden');
        chevron.src = '{% static "governance/img/chevron-up.svg" %}';
        assessmentBlockStates[blockNum] = true;
        updateAssessmentBlock(blockNum);
    }
}

let block1State = {
    prohibitedConfirmed: false,
    claimingException: '', // 'Yes' | 'No' | ''
    exceptionQualifies: '', // 'Yes' | 'No' | 'Not sure' | ''
    exceptionQualifiesMap: {}, // Mapping practice to 'Yes' | 'No' | 'Not sure'
    exceptionEvidenceMap: {}, // New: { [practiceName]: { link: '', files: [], explanation: '' } }
    exceptionEvidenceUploaded: false,
    exceptionEvidenceSavedLink: '',
    exceptionEvidenceFiles: [], // Array of {name, url, path, size}
    noExceptionConfirmed: false,
    be_assessment: null // Store BE assessment results for reference
};

let block2State = {
    highRiskConfirmed: false,
    uiConfirmedInSession: false, // Local session flag to force confirmation prompt
    materialInfluence: '', // 'Yes' | 'No' | 'Not sure' | ''
    narrowTasks: [], // Array of task strings
    profiling: '', // 'Yes' | 'No' | 'Unknown' | ''
    exemptionEvidenceUploaded: false,
    exemptionEvidenceSavedLink: '',
    be_assessment: null // Store BE assessment results for reference
};

let block3State = {
    transparencyConfirmed: false,
    exceptionOptions: [], // Array of selected exception options
    transparencyEvidenceUploaded: false,
    transparencyEvidenceSavedLink: '',
    be_assessment: null // Store BE assessment results for reference
};

let block4State = {
    gpaiConfirmed: false,
    gpaiProviderAnswer: '', // 'Yes' | 'No' | 'Not sure' | ''
    be_assessment: null // Store BE assessment results for reference
};

// Prohibited Practices Mapping (from Block_1_Prohibited_Practices_Logic.md)
const prohibitedPracticesMap = {
    'Subliminal / manipulative / deceptive techniques that materially distort behaviour and are likely to cause significant harm': {
        'label': 'Subliminal/manipulative/deceptive techniques',
        'article': '5(1)(a)',
        'has_exception': false,
        'exception_condition': null
    },
    'Exploitation of vulnerabilities (age, disability, or social / economic situation) to distort behaviour likely causing significant harm': {
        'label': 'Exploitation of vulnerabilities',
        'article': '5(1)(b)',
        'has_exception': false,
        'exception_condition': null
    },
    'Social scoring leading to detrimental / unfavourable treatment (esp. unjustified / disproportionate)': {
        'label': 'Social scoring',
        'article': '5(1)(c)',
        'has_exception': false,
        'exception_condition': null
    },
    'Criminal offence risk assessment / prediction based solely on profiling or personality traits (individual predictive policing)': {
        'label': 'Criminal offence risk assessment',
        'article': '5(1)(d)',
        'has_exception': true,
        'exception_condition': 'AI system is used to support a human assessment based on objective and verifiable facts directly linked to criminal activity (not solely profiling). (Art.5(1)(d))'
    },
    'Untargeted scraping of facial images from the internet or CCTV to build / expand facial recognition databases': {
        'label': 'Untargeted facial image scraping',
        'article': '5(1)(e)',
        'has_exception': false,
        'exception_condition': null
    },
    'Emotion recognition in the workplace or in education settings': {
        'label': 'Emotion recognition in workplace/education',
        'article': '5(1)(f)',
        'has_exception': true,
        'exception_condition': 'AI system is for medical or safety reasons. (Art.5(1)(f))'
    },
    'Biometric categorisation that infers or predicts sensitive traits (e.g., race, political opinions, religion, trade union membership, sexual orientation)': {
        'label': 'Biometric categorisation (sensitive traits)',
        'article': '5(1)(g)',
        'has_exception': true,
        'exception_condition': 'AI system is for labelling or filtering of lawfully acquired biometric datasets, such as images, based on biometric data or categorizing of biometric data in the area of law enforcement. (Art.5(1)(g))'
    },
    'Real-time remote biometric identification (RBI) in publicly accessible spaces for law enforcement purposes': {
        'label': 'Real-time remote biometric identification (RBI)',
        'article': '5(1)(h)',
        'has_exception': true,
        'exception_condition': 'Only if strictly necessary for one of the listed objectives (victims / imminent serious threat / serious crime suspect) and with safeguards + authorisation requirements (Art. 5(2)–(7)).'
    }
};

// Helper function to determine if Block 1 resulted in Prohibited
function isBlock1Prohibited() {
    const status = getProhibitedStatus();
    return status === 'Prohibited';
}

// Assessment Status Calculation Functions - Now pure getters from BE state
function getProhibitedStatus() {
    if (block1State.be_assessment && block1State.be_assessment.status) {
        return block1State.be_assessment.status;
    }
    return 'Not assessed';
}

function getHighRiskStatus() {
    // If Block 1 is Prohibited, Block 2 is de-activated
    if (isBlock1Prohibited()) {
        return 'De-activated';
    }
    
    if (block2State.be_assessment && block2State.be_assessment.status) {
        return block2State.be_assessment.status;
    }
    
    return 'Not assessed';
}

function getTransparencyStatus() {
    // If Block 1 is Prohibited, Block 3 is de-activated
    if (isBlock1Prohibited()) {
        return 'De-activated';
    }
    
    if (block3State.be_assessment && block3State.be_assessment.status) {
        return block3State.be_assessment.status;
    }

    return 'Not assessed';
}

function getGPAIStatus() {
    // If Block 1 is Prohibited, Block 4 is de-activated
    if (isBlock1Prohibited()) {
        return 'De-activated';
    }
    
    // Get integration from local input to handle immediate Profile changes
    const gpaiIntegration = document.querySelector('input[name="gpai_integration"]:checked')?.value || '';
    
    if (gpaiIntegration === 'Unknown') return 'Needs Review';
    if (gpaiIntegration === 'No') return 'Not Applicable';
    
    // For "Yes" integration, handle optimistic confirmation and provider answer
    if (gpaiIntegration === 'Yes') {
        if (block4State.gpaiConfirmed) {
            if (block4State.gpaiProviderAnswer === 'Yes') return 'Applies';
            if (block4State.gpaiProviderAnswer === 'No') return 'Not Applicable';
            return 'Needs Review';
        }
        return 'Triggered';
    }
    
    if (block4State.be_assessment && block4State.be_assessment.status) {
        return block4State.be_assessment.status;
    }

    return 'Not assessed';
}

function getStatusColorClass(status) {
    const statusColors = {
        'PASS': 'bg-[#E8F5E9] text-[#2E7D32]',
        'Not Prohibited': 'bg-[#E8F5E9] text-[#2E7D32]',
        'Triggered': 'bg-[#FFF3E0] text-[#E65100]',
        'High-risk': 'bg-[#FFF3E0] text-[#E65100]',
        'Prohibited': 'bg-[#FFEBEE] text-[#C62828]',
        'Exception claimed': 'bg-[#E8F5E9] text-[#2E7D32]',
        'Needs Review': 'bg-[#FFF9E6] text-[#F57C00]',
        'Not assessed': 'bg-[#F0F1F2] text-[#6B7280]',
        'De-activated': 'bg-[#F0F1F2] text-[#B5BCC4]',
        'Applies': 'bg-[#FFF3E0] text-[#E65100]',
        'Not Applicable': 'bg-[#E8F5E9] text-[#2E7D32]',
        'Not high-risk': 'bg-[#E8F5E9] text-[#2E7D32]',
        'Pending': 'bg-[#FFF9E6] text-[#F57C00]'
    };
    return statusColors[status] || 'bg-[#F0F1F2] text-[#6B7280]';
}

function updateAssessmentBlock(blockNum) {
    let status = '';
    let content = '';
    let details = null;
    
    switch(blockNum) {
        case 1:
            status = getProhibitedStatus();
            content = renderBlock1Content(status);
            break;
        case 2:
            // Try to get status from BE assessment first
            if (block2State.be_assessment) {
                status = block2State.be_assessment.status || getHighRiskStatus();
                details = block2State.be_assessment.details || null;
            } else {
                status = getHighRiskStatus();
            }
            content = renderBlock2Content(status, details);
            break;
        case 3:
            // Try to get status from BE assessment first
            if (block3State.be_assessment) {
                status = block3State.be_assessment.status || getTransparencyStatus();
                details = block3State.be_assessment.details || null;
            } else {
                status = getTransparencyStatus();
            }
            content = renderBlock3Content(status, details);
            break;
        case 4:
            // Try to get status from BE assessment first
            if (block4State.be_assessment) {
                status = block4State.be_assessment.status || getGPAIStatus();
                details = block4State.be_assessment.details || null;
            } else {
                status = getGPAIStatus();
            }
            content = renderBlock4Content(status, details);
            break;
    }
    
    // Update status badge
    const statusEl = document.getElementById(`block-${blockNum}-status`);
    if (statusEl) {
        statusEl.textContent = status;
        statusEl.className = `px-4 py-1.5 rounded-full font-semibold text-sm ${getStatusColorClass(status)}`;
    }
    
    // Update content
    const contentEl = document.getElementById(`block-${blockNum}-content-inner`);
    if (contentEl) {
        contentEl.innerHTML = content;
    }
}

function renderConfirmProfileInput(selectedPractices, practicesInfo, showButtons = true) {
    // Generate Article Summary
    const articles = selectedPractices.map(p => {
        const info = practicesInfo[p] || prohibitedPracticesMap[p] || {article: null};
        return info.article ? `Art. ${info.article}` : null;
    }).filter(a => a);
    
    let articleSummary = '';
    if (articles.length > 0) {
        const uniqueArticles = [...new Set(articles)];
        articleSummary = `This is a prohibited practice under ${uniqueArticles.map(a => `${a} of the EU AI Act`).join(', ')}`;
    } else {
        articleSummary = 'This is a prohibited practice under the EU AI Act.';
    }

    // Render content
    let html = `
        <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-5 mb-4 shadow-sm">
            <div class="mb-4">
                <p class="font-bold text-sm text-[#22262A] mb-2">Confirm Profile input:</p>
                <p class="font-normal text-sm text-[#464E58] mb-2">
                    You indicated the system uses the following capabilities or practices:
                </p>
                <div class="pl-4 space-y-2 mb-3">
                    ${selectedPractices.map(p => `<p class="font-normal text-sm text-[#22262A] leading-relaxed">${p}</p>`).join('')}
                </div>
                <p class="font-normal text-sm text-[#464E58]">
                    ${articleSummary}
                </p>
            </div>
    `;
    
    if (showButtons) {
        html += `<p class="font-bold text-sm text-[#22262A] mb-4">Do you confirm?</p>
                </div> <!-- End of content div -->
                <div class="flex justify-end gap-3">
                    <button onclick="confirmProhibited(false)" class="px-6 py-2.5 bg-white border border-[#B5BCC4] text-[#464E58] rounded-lg font-semibold text-sm hover:bg-[#F0F1F2] transition-colors">
                        Edit Profile Info
                    </button>
                    <button onclick="confirmProhibited(true)" class="px-6 py-2.5 bg-[#F13D30] text-white rounded-lg font-semibold text-sm hover:bg-[#DC180A] transition-colors">
                        Confirm
                    </button>
                </div>`;
    } else {
        html += `</div>`;
    }
    
    return html;
}

function renderBlock1Content(status) {
    if (status === 'Not assessed') {
        return '<p class="font-normal text-sm text-[#464E58]">Please complete Section 7 (Capabilities) in Profile to assess prohibited practices.</p>';
    }
    
    if (status === 'PASS') {
        return `
            <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#2E7D32] mb-2">✓ No prohibited practices detected</p>
                <p class="font-normal text-sm text-[#464E58] mt-2">
                    Based on your Profile inputs, this AI system does not appear to fall under the prohibited practices defined in Article 5 of the EU AI Act.
                </p>
            </div>
        `;
    }
    
    // Shared logic for getting selected practices (needed for Triggered and Prohibited)
    let selectedPractices = [];
    let practicesInfo = {};
    if (block1State.be_assessment && block1State.be_assessment.selected_practices) {
        selectedPractices = block1State.be_assessment.selected_practices;
        practicesInfo = block1State.be_assessment.practices_info || {};
    } else {
         // Fallback from DOM
         selectedPractices = Array.from(document.querySelectorAll('input[name="capability_practices"]:checked'))
                .map(cb => cb.value)
                .filter(v => v !== 'None of the above');
         
         selectedPractices.forEach(p => {
             if (prohibitedPracticesMap[p]) {
                 practicesInfo[p] = prohibitedPracticesMap[p];
             }
         });
    }
    
    // For Triggered or Prohibited, we often use the detailed view components
    
    if (status === 'Triggered') {
        if (!block1State.prohibitedConfirmed) {
            // Not confirmed yet: Show Confirm UI with buttons
            return `<div class="space-y-4">` + renderConfirmProfileInput(selectedPractices, practicesInfo, true) + `</div>`;
        } else {
            // Confirmed but still Triggered (likely waiting for Exception Claim answer)
            // Show Read-only Input + Exception Flow
            return `<div class="space-y-4">` + 
                   renderConfirmProfileInput(selectedPractices, practicesInfo, false) + 
                   renderBlock1ExceptionFlow(selectedPractices, practicesInfo) + 
                   `</div>`;
        }
    }
    
    if (status === 'Exception claimed') {
        const confirmedBanner = `
            <div class="w-full bg-[#E8F5E9] border border-[#81C784] rounded-lg p-3 mb-4">
                <p class="font-semibold text-sm text-[#2E7D32]">✓ Confirmed</p>
            </div>
        `;
        
        const practicesWithException = selectedPractices.filter(practice => {
            const info = practicesInfo[practice] || prohibitedPracticesMap[practice];
            return info && info.has_exception;
        });

        const successItems = practicesWithException.map(p => {
            const info = practicesInfo[p] || prohibitedPracticesMap[p];
            const conditionText = info.exception_condition || info.exceptionCondition || 'Exception available';
            return `
                <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-4 mb-3">
                    <p class="font-bold text-sm text-[#2E7D32] mb-1">✓ Exception Claimed: ${p}</p>
                    <p class="text-xs text-[#464E58] mb-2">${conditionText}</p>
                    <p class="font-normal text-sm text-[#464E58]">
                        Your exception claim has been recorded with supporting evidence. This will be subject to regulatory review.
                    </p>
                </div>
            `;
        }).join('');

        return `<div class="space-y-4">` + 
               renderConfirmProfileInput(selectedPractices, practicesInfo, false) + 
               confirmedBanner + 
               successItems + 
               `</div>`;
    }
    
    if (status === 'Prohibited') {
        const confirmedBanner = `
            <div class="w-full bg-[#E8F5E9] border border-[#81C784] rounded-lg p-3 mb-4">
                <p class="font-semibold text-sm text-[#2E7D32]">✓ Confirmed</p>
            </div>
        `;
        
        const prohibitedItems = selectedPractices.map(p => {
             const info = practicesInfo[p] || prohibitedPracticesMap[p];
             const hasException = info && info.has_exception;
             const answer = block1State.exceptionQualifiesMap[p];
             
             let reasonText = "Your AI System is Prohibited under Art.5 because of this practice.";
             let statusTitle = "Result: Prohibited Practice Detected";
             
             if (!hasException) {
                 reasonText = "This practice does not allow any exceptions under the EU AI Act.";
             } else if (answer === 'No') {
                 reasonText = "You stated that the system does NOT fall under the allowed exception conditions for this practice.";
             }

             return `
                <div class="bg-[#FFF5F5] border border-[#F13D30] rounded-lg p-4 mb-3">
                    <p class="font-bold text-sm text-[#F13D30] mb-2">${statusTitle}</p>
                    <p class="font-semibold text-sm text-[#22262A] mb-1">${p}</p>
                    <p class="font-normal text-sm text-[#464E58]">
                        ${reasonText} You need to redesign or remove this feature to ensure compliance.
                    </p>
                </div>
            `;
        }).join('');

        if (selectedPractices.length > 0) {
            return `<div class="space-y-4">` + 
                   renderConfirmProfileInput(selectedPractices, practicesInfo, false) + 
                   confirmedBanner + 
                   prohibitedItems + 
                   `</div>`;
        }
        
        return `<div class="bg-[#FFF5F5] border border-[#F13D30] rounded-lg p-4">
                <p class="font-bold text-sm text-[#F13D30] mb-2">Result: Prohibited</p>
                <p class="font-normal text-sm text-[#464E58]">
                    Your AI System is Prohibited under Art.5. You need to redesign or remove certain features to make it comply with the EU AI Act.
                </p>
            </div>`;
    }
    
    if (status === 'Needs Review') {
        const confirmedBanner = `
            <div class="w-full bg-[#E8F5E9] border border-[#81C784] rounded-lg py-2.5 px-4 mb-4 flex items-center gap-2 shadow-sm">
                <svg class="w-4 h-4 text-[#2E7D32]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
                </svg>
                <p class="font-semibold text-sm text-[#2E7D32]">Confirmed</p>
            </div>
        `;

        const needsReviewBanner = `
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-5 mb-4 shadow-sm">
                <p class="font-bold text-sm text-[#F57C00] mb-2 uppercase tracking-wide">Result: Needs Review</p>
                <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                    This system requires legal review to determine if the exception applies. Please consult with your legal team or compliance officer.
                </p>
            </div>
        `;

        if (selectedPractices.length > 0) {
            return `<div class="space-y-4">` + 
                   renderConfirmProfileInput(selectedPractices, practicesInfo, false) + 
                   confirmedBanner +
                   needsReviewBanner + 
                   `</div>`;
        }
        
        return needsReviewBanner;
    }
    
    return '<p class="text-sm text-[#464E58]">Status: ' + status + '</p>';
}

// Render exception flow content
function renderBlock1ExceptionFlow(selectedPractices, practicesInfo = {}) {
    // Confirmed state banner
    const confirmedBanner = `
        <div class="w-full bg-[#E8F5E9] border border-[#81C784] rounded-lg py-2.5 px-4 mb-4 flex items-center gap-2">
            <svg class="w-4 h-4 text-[#2E7D32]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
            </svg>
            <p class="font-semibold text-sm text-[#2E7D32]">Confirmed</p>
        </div>
    `;

    // 1. Check if ANY practice has NO exception available
    const practicesWithNoException = selectedPractices.filter(practice => {
        const info = practicesInfo[practice] || prohibitedPracticesMap[practice];
        return info && !info.has_exception;
    });
    
    if (practicesWithNoException.length > 0) {
        return `
            ${confirmedBanner}
            <div class="bg-[#FFEBEE] border border-[#EF5350] rounded-lg p-4 shadow-sm">
                <p class="font-bold text-sm text-[#C62828] mb-2">No exception available</p>
                <p class="font-normal text-sm text-[#464E58] mb-4">
                    This prohibited practice does not allow exceptions under the EU AI Act.
                </p>
                <div class="flex justify-end">
                    <button onclick="acknowledgeNoException()" class="px-6 py-2.5 bg-[#F13D30] text-white rounded-lg font-semibold text-sm hover:bg-[#DC180A] transition-colors">
                        Confirm
                    </button>
                </div>
            </div>
        `;
    }
    
    // 2. Exception Available → Exception Claim UI
    const practicesWithException = selectedPractices.filter(practice => {
        const info = practicesInfo[practice] || prohibitedPracticesMap[practice];
        return info && info.has_exception;
    });
    
    if (practicesWithException.length > 0) {
        const exceptionBlocks = practicesWithException.map((p, index) => {
            const info = practicesInfo[p] || prohibitedPracticesMap[p];
            const conditionText = info.exception_condition || info.exceptionCondition || 'Exception available';
            const currentAnswer = block1State.exceptionQualifiesMap[p] || '';
            
            let fullPracticeText = p;
            for (const key in prohibitedPracticesMap) {
                if (prohibitedPracticesMap[key].label === p) {
                    fullPracticeText = key;
                    break;
                }
            }

            let statusBadge = '';
            if (currentAnswer === 'Yes') {
                statusBadge = '<span class="px-2 py-1 bg-[#E8F5E9] text-[#2E7D32] text-[10px] font-bold rounded uppercase">Yes</span>';
            } else if (currentAnswer === 'No') {
                statusBadge = '<span class="px-2 py-1 bg-[#FEEDEC] text-[#DC180A] text-[10px] font-bold rounded uppercase">No</span>';
            } else if (currentAnswer === 'Not sure') {
                statusBadge = '<span class="px-2 py-1 bg-[#FFF9E6] text-[#F57C00] text-[10px] font-bold rounded uppercase">Not sure</span>';
            }

            let evidenceForm = '';
            if (currentAnswer === 'Yes') {
                const evidenceData = block1State.exceptionEvidenceMap[p] || { link: '', files: [], explanation: '' };
                evidenceForm = `
                    <div class="mt-4 pt-4 border-t border-[#F13D30]/20">
                        <label class="block text-sm font-semibold text-[#22262A] mb-2">
                            Evidence / Documentation for "${p}" <span class="text-[#F13D30]">*</span>
                        </label>
                        <p class="text-xs text-[#464E58] mb-3">Paste a link or upload new document below for this specific practice.</p>
                        <div class="flex gap-3 mb-3">
                            <input type="text" id="link-${index}" placeholder="Paste link here" value="${evidenceData.link || ''}"
                                class="flex-1 px-3 py-2 border border-[#D1D5DB] rounded-lg text-sm text-[#464E58]">
                            <button onclick="saveBlock1EvidenceLink('${p}', ${index})" class="px-4 py-2 bg-[#F13D30] text-white rounded-lg font-semibold text-xs hover:bg-[#DC180A]">Save link</button>
                        </div>
                        <div id="file-list-${index}" class="space-y-2 mb-3">
                            ${(evidenceData.files || []).map((file, fIdx) => `
                                <div class="flex items-center justify-between p-2 bg-gray-50 rounded-lg border border-gray-200">
                                    <span class="text-xs text-gray-600 truncate">${file.name}</span>
                                    <button onclick="removeBlock1EvidenceFile(${fIdx}, '${p}')" class="text-gray-400 hover:text-red-500">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"></path></svg>
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <input type="file" id="file-input-${index}" class="hidden" onchange="handleBlock1FileUpload(this, '${p}')">
                        <button onclick="document.getElementById('file-input-${index}').click()" class="w-full px-4 py-2 border-2 border-dashed border-[#D1D5DB] rounded-lg text-xs text-[#464E58] hover:border-[#F13D30] hover:bg-[#FFF5F5] transition-colors flex items-center justify-center gap-2 mb-3">
                            Upload Supporting Documents
                        </button>
                        <textarea id="explanation-${index}" rows="2" placeholder="Explanation..." onchange="updateBlock1Explanation('${p}', this.value)" class="w-full px-3 py-2 border border-[#D1D5DB] rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[#F13D30] resize-none">${evidenceData.explanation || ''}</textarea>
                    </div>
                `;
            }

            return `
                <div class="bg-[#FFF5F5] border border-[#F13D30] rounded-lg p-4 mb-4 relative shadow-sm">
                    <div class="flex justify-between items-start mb-3">
                        <p class="font-bold text-sm text-[#22262A]">Exception Claim</p>
                        ${statusBadge}
                    </div>
                    <p class="font-normal text-sm text-[#464E58] mb-3">Does your system “${fullPracticeText}” fall under the following condition?</p>
                    <div class="mb-4">
                        <input type="text" id="exception-condition-${index}" readonly class="w-full px-3 py-2 border border-[#D1D5DB] rounded-lg text-[#22262A] bg-white text-sm" value="${conditionText}">
                    </div>
                    <div class="flex gap-6">
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="exception_claim_radio_${index}" value="Yes" class="w-4 h-4 text-[#F13D30]" ${currentAnswer === 'Yes' ? 'checked' : ''} onchange="handleExceptionClaimChange('${p}', this.value)">
                            <span class="text-sm text-[#464E58]">Yes</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="exception_claim_radio_${index}" value="No" class="w-4 h-4 text-[#F13D30]" ${currentAnswer === 'No' ? 'checked' : ''} onchange="handleExceptionClaimChange('${p}', this.value)">
                            <span class="text-sm text-[#464E58]">No</span>
                        </label>
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="radio" name="exception_claim_radio_${index}" value="Not sure" class="w-4 h-4 text-[#F13D30]" ${currentAnswer === 'Not sure' ? 'checked' : ''} onchange="handleExceptionClaimChange('${p}', this.value)">
                            <span class="text-sm text-[#464E58]">Not sure</span>
                        </label>
                    </div>
                    ${evidenceForm}
                </div>
            `;
        }).join('');

        const hasNotSure = Object.values(block1State.exceptionQualifiesMap).includes('Not sure');
        const needsReviewBanner = hasNotSure ? `
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-5 mb-4 shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-300">
                <p class="font-bold text-sm text-[#F57C00] mb-2 uppercase tracking-wide">Result: Needs Review</p>
                <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                    This system requires legal review to determine if the exception applies. Please consult with your legal team or compliance officer.
                </p>
            </div>
        ` : '';

        const finalConfirmButton = `
            <div class="flex justify-end mt-4">
                <button onclick="confirmBlock1ExceptionClaim()" class="px-8 py-3 bg-[#F13D30] text-white rounded-lg font-bold text-sm hover:bg-[#DC180A] transition-all shadow-md">
                    Confirm Exception Claim
                </button>
            </div>
        `;

        return `
            ${confirmedBanner}
            ${exceptionBlocks}
            ${needsReviewBanner}
            ${finalConfirmButton}
        `;
    }
    return '';
}

// Render evidence upload form for Exception Claim "Yes" case
function renderBlock1ExceptionEvidenceForm(selectedPractices, practicesInfo = {}) {
    const confirmedBanner = `
        <div class="w-full bg-[#E8F5E9] border border-[#81C784] rounded-lg p-3 mb-4">
            <p class="font-semibold text-sm text-[#2E7D32]">✓ Confirmed</p>
        </div>
    `;
    
    return `
        ${confirmedBanner}
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-[#22262A] mb-2">
                    Evidence / Documentation <span class="text-[#F13D30]">*</span>
                </label>
                <p class="text-sm text-[#464E58] mb-3">Paste a link or upload new document below.</p>
                
                <div class="flex gap-3 mb-3">
                    <input type="text" id="block1-evidence-link" placeholder="Paste link here" 
                        class="flex-1 px-3 py-2 border border-[#D1D5DB] rounded-lg text-sm text-[#464E58] focus:outline-none focus:ring-2 focus:ring-[#F13D30]">
                    <button onclick="saveBlock1EvidenceLink()" 
                        class="px-6 py-2 bg-[#F13D30] text-white rounded-lg font-semibold text-sm hover:bg-[#DC180A] transition-colors">
                        Save link
                    </button>
                </div>
                
                <div id="block1-file-list" class="space-y-2 mb-3">
                    ${block1State.exceptionEvidenceFiles.map((file, idx) => `
                        <div class="flex items-center justify-between p-2 bg-gray-50 rounded-lg border border-gray-200">
                            <div class="flex items-center gap-2 overflow-hidden">
                                <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                                <span class="text-sm text-gray-600 truncate">${file.name}</span>
                            </div>
                            <button onclick="removeBlock1EvidenceFile(${idx})" class="text-gray-400 hover:text-red-500">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                    `).join('')}
                </div>
                
                <input type="file" id="block1-evidence-file-input" class="hidden" onchange="handleBlock1FileUpload(this)">
                <button onclick="document.getElementById('block1-evidence-file-input').click()" 
                    class="w-full px-4 py-3 border-2 border-dashed border-[#D1D5DB] rounded-lg text-sm text-[#464E58] hover:border-[#F13D30] hover:bg-[#FFF5F5] transition-colors flex items-center justify-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                    </svg>
                    Upload Supporting Documents
                </button>
            </div>
            
            <div>
                <textarea id="block1-evidence-explanation" rows="4" placeholder="Explain how the evidence supports your exception claim." 
                    class="w-full px-3 py-2 border border-[#D1D5DB] rounded-lg text-sm text-[#464E58] focus:outline-none focus:ring-2 focus:ring-[#F13D30] resize-none"></textarea>
            </div>
            
            <div class="flex justify-end">
                <button onclick="confirmBlock1ExceptionClaim()" 
                    class="px-6 py-2.5 bg-[#F13D30] text-white rounded-lg font-semibold text-sm hover:bg-[#DC180A] transition-colors">
                    Confirm Exception Claim
                </button>
            </div>
        </div>
    `;
}

// Helper functions for Block 1 exception flow
function acknowledgeNoException() {
    setClaimingException('No');
}

async function handleExceptionClaimChange(practiceName, value) {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    // Update local state map
    block1State.exceptionQualifiesMap[practiceName] = value;
    
    try {
        // Collect all exception condition texts
        const conditionInputs = document.querySelectorAll('[id^="exception-condition-"]');
        const exceptionConditions = Array.from(conditionInputs).map(input => input.value).filter(v => v);
        
        // Send the complete map to BE
        const response = await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                claiming_exception: 'Yes',
                exception_qualifies_map: block1State.exceptionQualifiesMap,
                exception_conditions: exceptionConditions
            })
        });
        const result = await response.json();
        
        if (result.success) {
            block1State.claimingException = 'Yes';
            block1State.exceptionQualifies = value;
            if (result.assessment && result.assessment.block1) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(1);
            }
        }
    } catch(e) { console.error(e); }
}

// Evidence handling functions for Block 1
async function saveBlock1EvidenceLink(practiceName, index) {
    const input = document.getElementById(`link-${index}`);
    const link = input ? input.value.trim() : '';
    if (!link) {
        showNotification('Please enter a link', 'warning');
        return;
    }

    if (!block1State.exceptionEvidenceMap[practiceName]) {
        block1State.exceptionEvidenceMap[practiceName] = { link: '', files: [], explanation: '' };
    }
    block1State.exceptionEvidenceMap[practiceName].link = link;

    await updateBlock1EvidenceMapOnBE();
    showNotification('Evidence link saved for ' + practiceName, 'success');
}

function updateBlock1Explanation(practiceName, value) {
    if (!block1State.exceptionEvidenceMap[practiceName]) {
        block1State.exceptionEvidenceMap[practiceName] = { link: '', files: [], explanation: '' };
    }
    block1State.exceptionEvidenceMap[practiceName].explanation = value;
}

async function handleBlock1FileUpload(input, practiceName) {
    const files = Array.from(input.files);
    if (!files.length) return;

    const formData = new FormData();
    files.forEach(file => formData.append('file', file));
    formData.append('folder', 'governance/uploads/block1');

    try {
        const response = await fetch('/api/upload-file/', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success && result.files) {
            if (!block1State.exceptionEvidenceMap[practiceName]) {
                block1State.exceptionEvidenceMap[practiceName] = { link: '', files: [], explanation: '' };
            }
            // Append new files
            block1State.exceptionEvidenceMap[practiceName].files = [
                ...block1State.exceptionEvidenceMap[practiceName].files, 
                ...result.files
            ];
            
            await updateBlock1EvidenceMapOnBE();
            showNotification('Document uploaded for ' + practiceName, 'success');
            updateAssessmentBlock(1); // Re-render to show new file
        } else {
            alert('Upload failed: ' + (result.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('File upload failed:', err);
        alert('Error uploading file');
    }
}

async function removeBlock1EvidenceFile(fIdx, practiceName) {
    if (block1State.exceptionEvidenceMap[practiceName]) {
        block1State.exceptionEvidenceMap[practiceName].files.splice(fIdx, 1);
        await updateBlock1EvidenceMapOnBE();
        updateAssessmentBlock(1);
    }
}

async function updateBlock1EvidenceMapOnBE() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            exception_evidence_map: block1State.exceptionEvidenceMap
        })
    });
}

async function confirmBlock1ExceptionClaim() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;

    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                exception_evidence_map: block1State.exceptionEvidenceMap
            })
        });
        const result = await response.json();
        
        if (result.success) {
            updateAssessmentBlocksFromBE(result.assessment);
            updateAssessmentBlock(1);
            showNotification('Exception claim documentation updated', 'success');
        }
    } catch (err) {
        console.error('Failed to confirm exception claim:', err);
        showNotification('Error confirming exception claim', 'error');
    }
}

// Helper functions for Block 1 exception flow - Update BE state
async function confirmProhibited(confirmed) {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    if (!confirmed) {
        // Redirect to Profile tab
        switchTab('profile');
        return;
    }
    
    try {
        console.log('[DEBUG] confirmProhibited: Sending request to backend...');
        // Update BE state
        const response = await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prohibited_confirmed: true
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block1State.prohibitedConfirmed = true;
            // Update UI with new assessment results from BE
            if (result.assessment && result.assessment.block1) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(1);
            }
        } else {
            alert('Error confirming assessment: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error confirming prohibited:', error);
        alert('Error confirming assessment. Please try again.');
    }
}

async function acknowledgeNoException() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                no_exception_confirmed: true
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block1State.noExceptionConfirmed = true;
            if (result.assessment && result.assessment.block1) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(1);
            }
        }
    } catch (error) {
        console.error('Error acknowledging no exception:', error);
    }
}

async function setClaimingException(value) {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                claiming_exception: value
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block1State.claimingException = value;
            if (result.assessment && result.assessment.block1) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(1);
            }
        }
    } catch (error) {
        console.error('Error setting claiming exception:', error);
    }
}

async function setExceptionQualifies(value) {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                exception_qualifies: value
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block1State.exceptionQualifies = value;
            if (result.assessment && result.assessment.block1) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(1);
            }
        }
    } catch (error) {
        console.error('Error setting exception qualifies:', error);
    }
}

async function confirmExceptionEvidence() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    const fileInput = document.getElementById('exception-evidence-upload');
    const linkInput = document.getElementById('exception-evidence-link');
    
    let evidenceUploaded = false;
    let evidenceLink = '';
    
    // Check file upload
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
        // Upload file first
        try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('folder', 'governance/uploads');
            
            const uploadResponse = await fetch('/api/upload-file/', {
                method: 'POST',
                body: formData,
            });
            
            const uploadResult = await uploadResponse.json();
            if (uploadResult.success) {
                evidenceUploaded = true;
            }
        } catch (error) {
            console.error('Error uploading evidence file:', error);
        }
    }
    
    // Check link
    if (linkInput && linkInput.value && linkInput.value.trim()) {
        evidenceLink = linkInput.value.trim();
    }
    
    if (!evidenceUploaded && !evidenceLink) {
        alert('Please upload a document or provide a link.');
        return;
    }
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block1-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                exception_evidence_uploaded: evidenceUploaded,
                exception_evidence_saved_link: evidenceLink
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block1State.exceptionEvidenceUploaded = evidenceUploaded;
            block1State.exceptionEvidenceSavedLink = evidenceLink;
            if (result.assessment && result.assessment.block1) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(1);
            }
        } else {
            alert('Error saving evidence: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error confirming exception evidence:', error);
        alert('Error saving evidence. Please try again.');
    }
}

// Helper functions for Block 2
function isCondition1Met() {
    const safetyComponent = document.querySelector('input[name="safety_component"]:checked')?.value || '';
    const thirdPartyConformity = document.querySelector('input[name="third_party_conformity"]:checked')?.value || '';
    return safetyComponent === 'Yes' && thirdPartyConformity === 'Yes';
}

function isCondition2Met() {
    const sectorDomains = Array.from(document.querySelectorAll('input[name="sector_domain"]:checked')).map(cb => cb.value);
    return sectorDomains.some(sector => sector !== 'Other / not listed' && sector !== 'Other / not listed:');
}

function getHighRiskTrigger() {
    const cond1 = isCondition1Met();
    const cond2 = isCondition2Met();
    
    if (cond1 && cond2) return 'both';
    if (cond1) return 'condition1';
    if (cond2) return 'condition2';
    return 'none';
}

function renderBlock2Content(status, block2Details = null) {
    if (status === 'Not assessed') {
        const reason = block2Details?.reason || 'Please complete Section 4 (Intended Purpose) in Profile to assess high-risk classification.';
        return `<p class="font-normal text-sm text-[#464E58]">${reason}</p>`;
    }
    
    if (status === 'Not high-risk') {
        return `
            <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-6">
                <p class="font-semibold text-sm text-[#2E7D32]">✓ Not High-Risk</p>
                <p class="font-normal text-sm text-[#464E58] mt-3 leading-relaxed">
                    ${block2Details?.reason || 'Based on your Profile inputs, this AI system does not appear to be classified as high-risk under the EU AI Act.'}
                </p>
            </div>
        `;
    }
    
    if (status === 'De-activated') {
        return `
            <div class="bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg p-6">
                <p class="font-semibold text-sm text-[#B5BCC4]">This block is de-activated</p>
                <p class="font-normal text-sm text-[#B5BCC4] mt-3 leading-relaxed">
                    ${block2Details?.reason || 'No high-risk conditions met.'}
                </p>
            </div>
    const annexIIISteps = ['q1', 'q2', 'q3', 'evidence'];
    const isAnnexIIIFlow = (status === 'Needs Review' || status === 'Needs review') && annexIIISteps.includes(block2Details?.step);

    if ((status === 'Needs Review' || status === 'Needs review') && !isAnnexIIIFlow) {
        return `
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-semibold text-sm text-[#F57C00]">⚠️ Needs Review</p>
                <p class="font-normal text-sm text-[#464E58] mt-3 leading-relaxed">
                    ${block2Details?.reason || 'This assessment requires manual review by the compliance team.'}
                </p>
            </div>
        `;
    }
    
    if (status === 'High-risk' || isAnnexIIIFlow) {
        const trigger = block2Details?.trigger || getHighRiskTrigger();
        const step = block2Details?.step;
        
        // 1. If NOT confirmed in this SESSION yet, show confirmation card (Image 1)
        if (!block2State.uiConfirmedInSession) {
            const isCond1 = block2Details?.condition1 || isCondition1Met();
            const isCond2 = block2Details?.condition2 || isCondition2Met();
            
            let condTexts = [];
            if (isCond1) {
                condTexts.push('<p class="font-normal text-sm text-[#464E58]">It is a safety component requiring third-party conformity assessment (Section 4, Q3)</p>');
            }
            if (isCond2) {
                let sectors = block2Details?.selected_sectors || [];
                if (sectors.length === 0) {
                    sectors = Array.from(document.querySelectorAll('input[name="sector_domain"]:checked'))
                        .map(cb => cb.value)
                        .filter(s => s && s !== 'Other / not listed' && s !== 'Other / not listed:');
                }
                sectors.forEach(sector => {
                    condTexts.push(`<p class="font-normal text-sm text-[#464E58]">It is used in high-risk sectors: ${sector} (Section 4, Q2)</p>`);
                });
            }
            
            return `
                <div class="space-y-4">
                    <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6 shadow-sm">
                        <p class="font-bold text-sm text-[#22262A] mb-3">Confirm Profile input:</p>
                        <p class="font-normal text-sm text-[#464E58] mb-4 leading-relaxed">
                            Based on your Profile inputs, this AI system may be classified as high-risk because:
                        </p>
                        <div class="pl-6 mb-4 flex flex-col gap-3">
                            ${condTexts.join('')}
                        </div>
                        <p class="font-bold text-sm text-[#22262A]">Do you confirm?</p>
                    </div>
                    <div class="flex justify-end gap-3 mt-2 pr-1">
                        <button onclick="switchTab('profile')" class="px-6 py-2.5 bg-white border border-[#B5BCC4] text-[#464E58] rounded-lg font-bold text-sm hover:bg-[#F0F1F2] transition-colors shadow-sm">
                            Edit Profile Info
                        </button>
                        <button onclick="confirmHighRisk()" class="px-8 py-2.5 bg-[#F13D30] text-white rounded-lg font-bold text-sm hover:bg-[#DC180A] transition-colors shadow-sm">
                            Confirm
                        </button>
                    </div>
                </div>
            `;
        }
        
        // 2. After confirmation - Show Result (Condition 1) or Annex III (Condition 2)
        const isCond1 = block2Details?.condition1 || isCondition1Met();
        
        // If it's Condition 1 (Annex I) - show confirmed result banner (Image 3)
        // OR if it's both but we are at the end of the flow
        if (isCond1) {
            return `
                <div class="space-y-4">
                    <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                        <p class="font-semibold text-sm text-[#F97316] mb-2">High-risk Classification Confirmed</p>
                        <p class="font-normal text-sm text-[#464E58] mb-4">
                            This AI system is classified as high-risk because it is a safety component of a product requiring third-party conformity assessment.
                        </p>
                    </div>
                </div>
            `;
        } else {
            // Only Condition 2 (Annex III) - Show Exemption Test
            // Need to reconstruct the "Confirm Profile input" box logic here to show it as "history"
            const isCond2 = block2Details?.condition2 || isCondition2Met();
            
            let condTexts = [];
            // We know it's not Condition 1 here, so only check Condition 2
            if (isCond2) {
                let sectors = block2Details?.selected_sectors || [];
                if (sectors.length === 0) {
                    sectors = Array.from(document.querySelectorAll('input[name="sector_domain"]:checked'))
                        .map(cb => cb.value)
                        .filter(s => s && s !== 'Other / not listed' && s !== 'Other / not listed:');
                }
                sectors.forEach(sector => {
                    condTexts.push(`<p class="font-normal text-sm text-[#464E58]">It is used in high-risk sectors: ${sector} (Section 4, Q2)</p>`);
                });
            }

            return `
                <div class="space-y-4">
                    <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6 shadow-sm">
                        <p class="font-bold text-sm text-[#22262A] mb-3">Confirm Profile input:</p>
                        <p class="font-normal text-sm text-[#464E58] mb-4 leading-relaxed">
                            Based on your Profile inputs, this AI system may be classified as high-risk because:
                        </p>
                        <div class="pl-6 flex flex-col gap-3">
                            ${condTexts.join('')}
                        </div>
                    </div>

                    <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg px-4 py-3">
                         <p class="font-semibold text-sm text-[#2E7D32]">✓ Confirmed</p>
                    </div>
                    ${renderBlock2AnnexIII(step, block2Details)}
                </div>
            `;
        }
    }
    
    // Fallback for other statuses
    if (status === 'Triggered') {
        // Redirection for legacy support if needed, but should be handled by High-risk now
        return renderBlock2Content('High-risk', block2Details);
    }
    
    return '<p class="text-sm text-[#464E58]">Status: ' + status + '</p>';
}

// Render Annex III Exemption Test flow

function renderBlock2AnnexIII(step, block2Details) {
    const matInf = block2Details?.material_influence || block2State.materialInfluence;
    const narrowTasks = block2Details?.narrow_tasks || block2State.narrowTasks || [];
    const profVal = block2Details?.profiling || block2State.profiling;

    // Helper functions for styling
    const getRadioStyle = (selected, val) => selected === val 
        ? 'border-[#F13D30]' 
        : 'border-[#B5BCC4] group-hover:border-[#F13D30]';
    const getRadioInner = (selected, val) => selected === val 
        ? '<div class="w-2.5 h-2.5 bg-[#F13D30] rounded-full"></div>' 
        : '';
        
    // Q1 Logic
    let q1Banner = '';
    if (matInf === 'Yes') {
        q1Banner = `
            <div class="mt-6 bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-bold text-sm text-[#F97316] mb-2">Result: Exemption fails → High-Risk</p>
                <p class="font-normal text-sm text-[#464E58]">
                    This AI system is classified as high-risk under the EU AI Act and does not qualify for the Annex III exemption.
                </p>
            </div>`;
    } else if (matInf === 'Not sure') {
        q1Banner = `
             <div class="mt-6 bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-bold text-sm text-[#F97316]">Result: Needs Review</p>
            </div>`;
    }

    const q1HTML = `
        <div class="space-y-6">
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-bold text-sm text-[#22262A] mb-2">Annex III Exemption Test, Art. 6(3)</p>
                <p class="font-normal text-sm text-[#464E58]">
                    The system operates in a high-risk sector. Please complete the following assessment to determine if an exemption applies.
                </p>
            </div>

            <div>
                <p class="font-bold text-sm text-[#22262A] mb-4">
                    Q1. Does the system materially influence the outcome of decision-making OR pose significant risk to health / safety / fundamental rights? <span class="text-[#F13D30]">*</span>
                </p>
                
                <div class="relative pl-2">
                     <div class="absolute left-2 top-2 bottom-4 w-0.5 bg-[#B5BCC4] rounded-full"></div>

                     <div class="relative pl-8 pb-4">
                         <div class="absolute left-0 top-3 w-6 h-0.5 border-t-2 border-[#B5BCC4]"></div>
                         <button onclick="setMaterialInfluence('Yes')" class="text-left w-full group flex items-center gap-3">
                            <div class="w-4 h-4 border ${getRadioStyle(matInf, 'Yes')} rounded-full flex items-center justify-center transition-colors bg-white">
                                ${getRadioInner(matInf, 'Yes')}
                            </div>
                            <span class="text-sm text-[#464E58] group-hover:text-[#22262A]">Yes</span>
                         </button>
                     </div>
                     
                     <div class="relative pl-8 pb-4">
                         <div class="absolute left-0 top-3 w-6 h-0.5 border-t-2 border-[#B5BCC4]"></div>
                         <button onclick="setMaterialInfluence('No')" class="text-left w-full group flex items-center gap-3">
                            <div class="w-4 h-4 border ${getRadioStyle(matInf, 'No')} rounded-full flex items-center justify-center transition-colors bg-white">
                                ${getRadioInner(matInf, 'No')}
                            </div>
                            <span class="text-sm text-[#464E58] group-hover:text-[#22262A]">No</span>
                         </button>
                     </div>

                     <div class="relative pl-8">
                         <div class="absolute left-0 top-3 w-6 h-0.5 border-t-2 border-[#B5BCC4]"></div>
                         <button onclick="setMaterialInfluence('Not sure')" class="text-left w-full group flex items-center gap-3">
                            <div class="w-4 h-4 border ${getRadioStyle(matInf, 'Not sure')} rounded-full flex items-center justify-center transition-colors bg-white">
                                ${getRadioInner(matInf, 'Not sure')}
                            </div>
                            <span class="text-sm text-[#464E58] group-hover:text-[#22262A]">Not sure</span>
                         </button>
                     </div>
                </div>
                ${q1Banner}
            </div>
        </div>
    `;

    // If Q1 is not 'No', stop here
    if (matInf !== 'No') return q1HTML;

    // --- Q2 Logic ---
    const q2Options = [
        'Narrow procedural task',
        'Improves a previously completed human activity',
        'Detects patterns / deviations from past decisions (without influencing decisions)',
        'Preparatory task to an assessment relevant for the purposes of the use cases listed in Annex III (e.g., indexing, sorting, summarising)',
        'None of above'
    ];

    const hasNoneOfAbove = narrowTasks.includes('None of above');
    let q2Banner = '';
    if (hasNoneOfAbove) {
        q2Banner = `
            <div class="mt-6 bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-bold text-sm text-[#F97316] mb-2">Result: Exemption fails → High-Risk</p>
                <p class="font-normal text-sm text-[#464E58]">
                    This AI system is classified as high-risk under the EU AI Act and does not qualify for the Annex III exemption.
                </p>
            </div>`;
    }

    const q2Items = q2Options.map(opt => {
        const checked = narrowTasks.includes(opt);
        return `
            <div class="relative pl-8 pb-4 last:pb-0">
                <div class="absolute left-0 top-3 w-6 h-0.5 border-t-2 border-[#B5BCC4]"></div>
                <label class="flex items-start gap-3 cursor-pointer group">
                    <input type="checkbox" value="${opt}" ${checked ? 'checked' : ''} 
                           onchange="updateNarrowTasks(this)"
                           class="mt-0.5 w-4 h-4 text-[#F13D30] border-[#B5BCC4] rounded focus:ring-[#F13D30]">
                    <span class="text-sm text-[#464E58] group-hover:text-[#22262A] leading-tight">${opt}</span>
                </label>
            </div>
        `;
    }).join('');

    const q2HTML = `
        <div class="mt-8">
            <p class="font-bold text-sm text-[#22262A] mb-4">
                Q2. This AI system only does one of the following (select all that apply) <span class="text-[#F13D30]">*</span>
            </p>
            <div class="relative pl-2">
                 <div class="absolute left-2 top-2 bottom-4 w-0.5 bg-[#B5BCC4] rounded-full"></div>
                 ${q2Items}
            </div>
            ${q2Banner}
        </div>
    `;

    // If Q2 not done or invalid (none of above), return Q1 + Q2
    const hasValidTask = narrowTasks.length > 0 && !hasNoneOfAbove;
    if (!hasValidTask) return q1HTML + q2HTML;

    // --- Q3 Logic ---
    let q3Banner = '';
    if (profVal === 'Yes') {
        q3Banner = `
            <div class="mt-6 bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-bold text-sm text-[#F97316] mb-2">Result: Exemption fails → High-Risk</p>
            </div>`;
    } else if (profVal === 'Unknown') {
        q3Banner = `
            <div class="mt-6 bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-bold text-sm text-[#F97316]">Result: Needs Review</p>
            </div>`;
    }

    const q3HTML = `
        <div class="mt-8">
            <p class="font-bold text-sm text-[#22262A] mb-4">
                Q3. Does the system perform profiling of natural persons? <span class="text-[#F13D30]">*</span>
            </p>
            <div class="relative pl-2">
                 <div class="absolute left-2 top-2 bottom-4 w-0.5 bg-[#B5BCC4] rounded-full"></div>
                 
                 <div class="relative pl-8 pb-4">
                     <div class="absolute left-0 top-3 w-6 h-0.5 border-t-2 border-[#B5BCC4]"></div>
                     <button onclick="setProfiling('Yes')" class="text-left w-full group flex items-center gap-3">
                        <div class="w-4 h-4 border ${getRadioStyle(profVal, 'Yes')} rounded-full flex items-center justify-center transition-colors bg-white">
                            ${getRadioInner(profVal, 'Yes')}
                        </div>
                        <span class="text-sm text-[#464E58] group-hover:text-[#22262A]">Yes</span>
                     </button>
                 </div>
                 
                 <div class="relative pl-8 pb-4">
                     <div class="absolute left-0 top-3 w-6 h-0.5 border-t-2 border-[#B5BCC4]"></div>
                     <button onclick="setProfiling('No')" class="text-left w-full group flex items-center gap-3">
                        <div class="w-4 h-4 border ${getRadioStyle(profVal, 'No')} rounded-full flex items-center justify-center transition-colors bg-white">
                            ${getRadioInner(profVal, 'No')}
                        </div>
                        <span class="text-sm text-[#464E58] group-hover:text-[#22262A]">No</span>
                     </button>
                 </div>

                 <div class="relative pl-8">
                     <div class="absolute left-0 top-3 w-6 h-0.5 border-t-2 border-[#B5BCC4]"></div>
                     <button onclick="setProfiling('Unknown')" class="text-left w-full group flex items-center gap-3">
                        <div class="w-4 h-4 border ${getRadioStyle(profVal, 'Unknown')} rounded-full flex items-center justify-center transition-colors bg-white">
                            ${getRadioInner(profVal, 'Unknown')}
                        </div>
                        <span class="text-sm text-[#464E58] group-hover:text-[#22262A]">Unknown</span>
                     </button>
                 </div>
            </div>
            ${q3Banner}
        </div>
    `;

    return q1HTML + q2HTML + q3HTML;
}

// Block 2 API functions
async function confirmHighRisk() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block2-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                high_risk_confirmed: true
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block2State.highRiskConfirmed = true;
            block2State.uiConfirmedInSession = true; // Set session flag
            if (result.assessment && result.assessment.block2) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(2);
            }
        } else {
            alert('Error confirming assessment: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error confirming high-risk:', error);
        alert('Error confirming assessment. Please try again.');
    }
}

async function setMaterialInfluence(value) {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block2-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                material_influence: value
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block2State.materialInfluence = value;
            if (result.assessment && result.assessment.block2) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(2);
            }
        }
    } catch (error) {
        console.error('Error setting material influence:', error);
    }
}

function updateNarrowTasks(checkbox) {
    const val = checkbox.value;
    const isChecked = checkbox.checked;
    
    let current = block2State.narrowTasks || [];
    
    if (val === 'None of above') {
        // If selecting None, clear others. If deselecting, just clear.
        if (isChecked) {
            current = ['None of above'];
        } else {
            current = [];
        }
    } else {
        // Normal option
        if (isChecked) {
            // Remove 'None of above' if present
            current = current.filter(t => t !== 'None of above');
            current.push(val);
        } else {
            current = current.filter(t => t !== val);
        }
    }
    
    block2State.narrowTasks = current;
    // Auto-save
    confirmNarrowTasks();
}

async function confirmNarrowTasks() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block2-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                narrow_tasks: block2State.narrowTasks
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.assessment && result.assessment.block2) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(2);
            }
        }
    } catch (error) {
        console.error('Error confirming narrow tasks:', error);
    }
}

async function setProfiling(value) {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block2-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                profiling: value
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block2State.profiling = value;
            if (result.assessment && result.assessment.block2) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(2);
            }
        }
    } catch (error) {
        console.error('Error setting profiling:', error);
    }
}

async function confirmExemptionEvidence() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    const fileInput = document.getElementById('exemption-evidence-upload');
    const linkInput = document.getElementById('exemption-evidence-link');
    
    let evidenceUploaded = false;
    let evidenceLink = '';
    
    // Check file upload
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
        try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('folder', 'governance/uploads');
            
            const uploadResponse = await fetch('/api/upload-file/', {
                method: 'POST',
                body: formData,
            });
            
            const uploadResult = await uploadResponse.json();
            if (uploadResult.success) {
                evidenceUploaded = true;
            }
        } catch (error) {
            console.error('Error uploading evidence file:', error);
        }
    }
    
    // Check link
    if (linkInput && linkInput.value && linkInput.value.trim()) {
        evidenceLink = linkInput.value.trim();
    }
    
    if (!evidenceUploaded && !evidenceLink) {
        alert('Please upload a document or provide a link.');
        return;
    }
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block2-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                exemption_evidence_uploaded: evidenceUploaded,
                exemption_evidence_saved_link: evidenceLink
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block2State.exemptionEvidenceUploaded = evidenceUploaded;
            block2State.exemptionEvidenceSavedLink = evidenceLink;
            if (result.assessment && result.assessment.block2) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(2);
            }
        } else {
            alert('Error saving evidence: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error confirming exemption evidence:', error);
        alert('Error saving evidence. Please try again.');
    }
}

function renderBlock3Content(status, block3Details = null) {
    if (status === 'Not assessed') {
        const reason = block3Details?.reason || 'Please complete Section 7 (Capabilities) in Profile to assess transparency obligations.';
        return `<p class="font-normal text-sm text-[#464E58]">${reason}</p>`;
    }
    
    if (status === 'De-activated') {
        return `
            <div class="bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#B5BCC4]">This block is de-activated</p>
                <p class="font-normal text-sm text-[#B5BCC4] mt-2">
                    ${block3Details?.reason || 'Block 1 Prohibited - transparency obligation assessment not applicable.'}
                </p>
            </div>
        `;
    }
    
    if (status === 'Not Applicable') {
        return `
            <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#2E7D32]">✓ Not Applicable</p>
                <p class="font-normal text-sm text-[#464E58] mt-2">
                    ${block3Details?.reason || 'Transparency obligations do not apply (valid exceptions claimed with evidence).'}
                </p>
            </div>
        `;
    }
    
    if (status === 'Needs Review') {
        return `
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#F57C00]">⚠️ Needs Review</p>
                <p class="font-normal text-sm text-[#464E58] mt-2">
                    ${block3Details?.reason || 'This assessment requires manual review by the compliance team.'}
                </p>
            </div>
        `;
    }
    
    if (status === 'Applies') {
        return `
            <div class="bg-[#FFEBEE] border border-[#EF5350] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#C62828]">📋 Transparency Obligations Apply</p>
                <p class="font-normal text-sm text-[#464E58] mt-2">
                    ${block3Details?.reason || 'This AI system must comply with transparency obligations under EU AI Act Article 50.'}
                </p>
            </div>
        `;
    }
    
    // Status = 'Triggered' - Show confirmation or exception flow
    if (status === 'Triggered') {
        const triggers = block3Details?.triggers || [];
        
        // If not confirmed yet, show confirmation card
        if (!block3State.transparencyConfirmed) {
            const triggerReasons = getTransparencyTriggerReasons(triggers);
            const reasonsList = triggerReasons.map(reason => 
                `<li class="font-medium text-sm text-[#464E58] ml-2">${reason}</li>`
            ).join('');
            
            return `
                <div class="space-y-4">
                    <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-4">
                        <p class="font-semibold text-sm text-[#22262A] mb-2">Confirm Profile input:</p>
                        <p class="font-normal text-sm text-[#464E58] mb-2">
                            Based on your Profile inputs, transparency obligations may apply because:
                        </p>
                        <ul class="list-disc list-inside space-y-1 mb-4">
                            ${reasonsList}
                        </ul>
                        <p class="font-semibold text-sm text-[#22262A]">Do you confirm?</p>
                    </div>
                    <div class="flex justify-end gap-3">
                        <button onclick="switchTab('profile')" class="px-6 py-2.5 bg-white border border-[#B5BCC4] text-[#464E58] rounded-lg font-semibold text-sm hover:bg-[#F0F1F2] transition-colors">
                            Edit Profile Info
                        </button>
                        <button onclick="confirmTransparency()" class="px-6 py-2.5 bg-[#F13D30] text-white rounded-lg font-semibold text-sm hover:bg-[#DC180A] transition-colors">
                            Confirm
                        </button>
                    </div>
                </div>
            `;
        }
        
        // After confirmation - show exception selection flow
        return renderBlock3ExceptionFlow(triggers, block3Details);
    }
    
    return '<p class="text-sm text-[#464E58]">Status: ' + status + '</p>';
}

// Get transparency trigger reasons for display
function getTransparencyTriggerReasons(triggers) {
    const reasons = [];
    const capabilityPractices = Array.from(document.querySelectorAll('input[name="capability_practices"]:checked')).map(cb => cb.value);
    const interactsPersons = document.querySelector('input[name="interacts_persons"]:checked')?.value || '';
    const syntheticContent = Array.from(document.querySelectorAll('input[name="synthetic_content"]:checked')).map(cb => cb.value);
    const deploymentContext = document.querySelector('input[name="deployment_context"]:checked')?.value || '';
    const affectedOutputs = Array.from(document.querySelectorAll('input[name="affected_outputs"]:checked')).map(cb => cb.value);
    
    if (triggers.includes('case1')) {
        reasons.push('Uses biometric identification and categorisation (Section 4, Q2)');
    }
    if (triggers.includes('case2')) {
        reasons.push('Emotion recognition in the workplace or in education settings (Section 7, Q1)');
    }
    if (triggers.includes('case3')) {
        reasons.push('Biometric categorisation that infers or predicts sensitive traits (Section 7, Q1)');
    }
    if (triggers.includes('case4')) {
        reasons.push('Interacts directly with natural persons (Section 7, Q2)');
    }
    if (triggers.includes('case5')) {
        reasons.push('Generates or manipulates synthetic content (Section 7, Q3)');
    }
    if (triggers.includes('case6')) {
        if (affectedOutputs.includes('Citizens / residents') && deploymentContext === 'General public / consumer-facing') {
            reasons.push('Affects citizens / residents and is general public / consumer-facing (Section 5, Q1 & Q3)');
        } else if (affectedOutputs.includes('Citizens / residents')) {
            reasons.push('Affects citizens / residents (Section 5, Q3)');
        } else {
            reasons.push('General public / consumer-facing deployment (Section 5, Q1)');
        }
    }
    
    return reasons;
}

// Render exception selection flow
function renderBlock3ExceptionFlow(triggers, block3Details) {
    const caseGroups = block3Details?.case_groups || [];
    
    // Map triggers to groups
    const groups = [];
    if (triggers.includes('case1') || triggers.includes('case2') || triggers.includes('case3')) {
        groups.push({
            key: 'group1_2_3',
            label: 'For Biometric identification, Emotion recognition, Biometric categorisation:',
            options: [
                'Permitted by law to detect, prevent or investigate criminal offences, as stated in Art. 50(3)',
                'None of the above (no exception for biometric/emotion recognition cases)'
            ]
        });
    }
    if (triggers.includes('case4')) {
        groups.push({
            key: 'group4',
            label: 'For Direct interaction with persons:',
            options: [
                '"Obvious to the user" exception (no notice needed), as stated in Art. 50(1)',
                'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(1)',
                'None of the above (no exception for direct interaction case)'
            ]
        });
    }
    if (triggers.includes('case5')) {
        groups.push({
            key: 'group5',
            label: 'For Synthetic content generation / manipulation:',
            options: [
                'Deepfake labelling exception (e.g., artistic / satire / fiction), as stated in Art. 50(4)',
                'None of the above (no exception for synthetic content case)'
            ]
        });
    }
    if (triggers.includes('case6')) {
        groups.push({
            key: 'group6',
            label: 'For Citizens / residents or General public facing:',
            options: [
                'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(4)',
                'Human review is in place or a natural or legal person holds editorial responsibility for the publication of the content, as stated in Art. 50(4)',
                'None of the above (no exception for citizens/public-facing case)'
            ]
        });
    }
    
    // Check if all groups have exceptions selected
    const allGroupsHaveException = groups.every(group => {
        return block3State.exceptionOptions.some(opt => group.options.includes(opt));
    });
    
    // Check if evidence is needed (all groups have valid exceptions, not "None of above")
    const hasValidExceptionsForAll = groups.every(group => {
        return block3State.exceptionOptions.some(opt => 
            group.options.includes(opt) && !opt.includes('None of the above')
        );
    });
    
    const evidenceProvided = block3State.transparencyEvidenceUploaded || 
                            (block3State.transparencyEvidenceSavedLink && block3State.transparencyEvidenceSavedLink.trim());
    
    // If all groups have valid exceptions and evidence provided, show success
    if (hasValidExceptionsForAll && evidenceProvided) {
        return `
            <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#2E7D32]">✓ Not Applicable</p>
                <p class="font-normal text-sm text-[#464E58] mt-2">
                    Valid exceptions for all groups with evidence provided - transparency obligations do not apply.
                </p>
            </div>
        `;
    }
    
    // If all groups have valid exceptions but no evidence, show evidence section
    if (hasValidExceptionsForAll && !evidenceProvided) {
        return `
            <div class="space-y-4">
                <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-4">
                    <p class="font-semibold text-sm text-[#22262A] mb-2">Evidence Required</p>
                    <p class="font-normal text-sm text-[#464E58] mb-2">
                        To claim exceptions, please provide evidence (upload document or paste link).
                    </p>
                    <div class="mt-4 space-y-3">
                        <div>
                            <label class="block text-sm font-medium text-[#374151] mb-2">Upload Evidence Document</label>
                            <input type="file" id="transparency-evidence-upload" class="w-full px-3 py-2 border border-[#D1D5DB] rounded-lg">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-[#374151] mb-2">Or Paste Link</label>
                            <input type="text" id="transparency-evidence-link" placeholder="Paste link here" 
                                   value="${block3State.transparencyEvidenceSavedLink || ''}"
                                   class="w-full px-3 py-2 border border-[#D1D5DB] rounded-lg">
                        </div>
                    </div>
                </div>
                <div class="flex justify-end">
                    <button onclick="confirmTransparencyEvidence()" class="px-6 py-2.5 bg-[#F13D30] text-white rounded-lg font-semibold text-sm hover:bg-[#DC180A] transition-colors">
                        Confirm Evidence
                    </button>
                </div>
            </div>
        `;
    }
    
    // Show exception selection for each group
    const groupsHTML = groups.map(group => {
        const optionsHTML = group.options.map(option => {
            const checked = block3State.exceptionOptions.includes(option) ? 'checked' : '';
            return `
                <label class="flex items-center space-x-2 cursor-pointer">
                    <input type="radio" name="exception_${group.key}" value="${option}" ${checked} 
                           onchange="updateExceptionOption('${group.key}', '${option}')" 
                           class="w-4 h-4 text-[#F13D30] border-[#B5BCC4] focus:ring-[#F13D30]">
                    <span class="font-normal text-sm text-[#464E58]">${option}</span>
                </label>
            `;
        }).join('');
        
        return `
            <div class="border-b border-[#E5E7EB] pb-4 mb-4">
                <p class="font-semibold text-sm text-[#22262A] mb-3">${group.label}</p>
                <div class="space-y-2">
                    ${optionsHTML}
                </div>
            </div>
        `;
    }).join('');
    
    return `
        <div class="space-y-4">
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#22262A] mb-2">Exception Selection for Each Group</p>
                <p class="font-normal text-sm text-[#464E58] mb-4">
                    Select exception options for each triggered case group:
                </p>
                <div class="space-y-4">
                    ${groupsHTML}
                </div>
            </div>
            <div class="flex justify-end">
                <button onclick="confirmExceptionOptions()" class="px-6 py-2.5 bg-[#F13D30] text-white rounded-lg font-semibold text-sm hover:bg-[#DC180A] transition-colors">
                    Confirm Selections
                </button>
            </div>
        </div>
    `;
}

// Block 3 API functions
async function confirmTransparency() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block3-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transparency_confirmed: true
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block3State.transparencyConfirmed = true;
            if (result.assessment && result.assessment.block3) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(3);
            }
        } else {
            alert('Error confirming assessment: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error confirming transparency:', error);
        alert('Error confirming assessment. Please try again.');
    }
}

function updateExceptionOption(groupKey, option) {
    // Remove any existing option for this group
    const groupOptions = getGroupOptions(groupKey);
    block3State.exceptionOptions = block3State.exceptionOptions.filter(opt => !groupOptions.includes(opt));
    
    // Add new option
    if (!block3State.exceptionOptions.includes(option)) {
        block3State.exceptionOptions.push(option);
    }
    
    // Auto-save to BE when option changes
    confirmExceptionOptions();
}

function getGroupOptions(groupKey) {
    const allOptions = {
        'group1_2_3': [
            'Permitted by law to detect, prevent or investigate criminal offences, as stated in Art. 50(3)',
            'None of the above (no exception for biometric/emotion recognition cases)'
        ],
        'group4': [
            '"Obvious to the user" exception (no notice needed), as stated in Art. 50(1)',
            'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(1)',
            'None of the above (no exception for direct interaction case)'
        ],
        'group5': [
            'Deepfake labelling exception (e.g., artistic / satire / fiction), as stated in Art. 50(4)',
            'None of the above (no exception for synthetic content case)'
        ],
        'group6': [
            'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(4)',
            'Human review is in place or a natural or legal person holds editorial responsibility for the publication of the content, as stated in Art. 50(4)',
            'None of the above (no exception for citizens/public-facing case)'
        ]
    };
    return allOptions[groupKey] || [];
}

async function confirmExceptionOptions() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block3-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                exception_options: block3State.exceptionOptions
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.assessment && result.assessment.block3) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(3);
            }
        }
    } catch (error) {
        console.error('Error confirming exception options:', error);
    }
}

async function confirmTransparencyEvidence() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    const fileInput = document.getElementById('transparency-evidence-upload');
    const linkInput = document.getElementById('transparency-evidence-link');
    
    let evidenceUploaded = false;
    let evidenceLink = '';
    
    // Check file upload
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
        try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('folder', 'governance/uploads');
            
            const uploadResponse = await fetch('/api/upload-file/', {
                method: 'POST',
                body: formData,
            });
            
            const uploadResult = await uploadResponse.json();
            if (uploadResult.success) {
                evidenceUploaded = true;
            }
        } catch (error) {
            console.error('Error uploading evidence file:', error);
        }
    }
    
    // Check link
    if (linkInput && linkInput.value && linkInput.value.trim()) {
        evidenceLink = linkInput.value.trim();
    }
    
    if (!evidenceUploaded && !evidenceLink) {
        alert('Please upload a document or provide a link.');
        return;
    }
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block3-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transparency_evidence_uploaded: evidenceUploaded,
                transparency_evidence_saved_link: evidenceLink
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block3State.transparencyEvidenceUploaded = evidenceUploaded;
            block3State.transparencyEvidenceSavedLink = evidenceLink;
            if (result.assessment && result.assessment.block3) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(3);
            }
        } else {
            alert('Error saving evidence: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error confirming transparency evidence:', error);
        alert('Error saving evidence. Please try again.');
    }
}

function renderBlock4Content(status, block4Details = null) {
    if (status === 'Not assessed') {
        const reason = block4Details?.reason || 'Please complete Section 8 (Technical Profile) Q2 in Profile to assess GPAI applicability.';
        return `<p class="font-normal text-sm text-[#464E58]">${reason}</p>`;
    }
    
    if (status === 'De-activated') {
        return `
            <div class="bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#B5BCC4]">This block is de-activated</p>
                <p class="font-normal text-sm text-[#B5BCC4] mt-2">
                    ${block4Details?.reason || 'Block 1 Prohibited - GPAI obligation assessment not applicable.'}
                </p>
            </div>
        `;
    }

    let gpaiIntegration = block4Details?.gpai_integration || '';
    if (!gpaiIntegration) {
        gpaiIntegration = document.querySelector('input[name="gpai_integration"]:checked')?.value || '';
    }

    // Case: No integration
    if (gpaiIntegration === 'No') {
        return `
            <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-6">
                <p class="font-bold text-sm text-[#2E7D32]">✓ GPAI Obligations Not Applicable</p>
                <p class="font-normal text-sm text-[#464E58] mt-3 leading-relaxed">
                    Based on your Profile inputs, this AI system does not qualify as a general-purpose AI model, so GPAI obligations under Chapter V of the EU AI Act do not apply.
                </p>
            </div>
        `;
    }
    
    // Case: Unknown integration
    if (gpaiIntegration === 'Unknown') {
        return `
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6">
                <p class="font-bold text-sm text-[#F57C00] mb-3">Result: Needs Review</p>
                <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                    In your Profile (Section 8, Q2), you indicated that it is <strong>Unknown</strong> whether this system is provided as a general-purpose AI (GPAI) model/component or integrates one.
                </p>
                <p class="font-normal text-sm text-[#464E58] mt-3 leading-relaxed">
                    Please clarify this information to determine whether GPAI obligations under Chapter V of the EU AI Act apply to your system. Consult with your technical team or legal counsel for guidance.
                </p>
            </div>
        `;
    }

    // GPAI integration is "Yes"
    if (gpaiIntegration === 'Yes') {
        // Triggered state
        if (status === 'Triggered') {
            return `
                <div class="space-y-4">
                    <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6 shadow-sm">
                        <p class="font-bold text-sm text-[#22262A] mb-3">Confirm Profile input:</p>
                        <p class="font-normal text-sm text-[#464E58] mb-3">
                            Based on your Profile inputs, GPAI obligations apply to this AI system because:
                        </p>
                        <div class="pl-8 mb-4">
                             <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                                System is provided as or integrates a general-purpose AI (GPAI) model / component (Section 8, Q2)
                             </p>
                        </div>
                        <p class="font-bold text-sm text-[#22262A]">Do you confirm?</p>
                    </div>
                    <div class="flex justify-end gap-3 mt-2 pr-1">
                        <button onclick="switchTab('profile')" class="px-6 py-2.5 bg-white border border-[#B5BCC4] text-[#464E58] rounded-lg font-bold text-sm hover:bg-[#F0F1F2] transition-colors shadow-sm">
                            Edit Profile Info
                        </button>
                        <button onclick="confirmGPAI()" class="px-8 py-2.5 bg-[#F13D30] text-white rounded-lg font-bold text-sm hover:bg-[#DC180A] transition-colors shadow-sm">
                            Confirm
                        </button>
                    </div>
                </div>
            `;
        }

        // Confirmed flow (status is 'Needs Review', 'Applies', or 'Not Applicable')
        let html = '<div class="space-y-4">';
        
        // Static Profile Confirmation Box
        html += `
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6 shadow-sm">
                <p class="font-bold text-sm text-[#22262A] mb-3">Confirm Profile input:</p>
                <p class="font-normal text-sm text-[#464E58] mb-3">
                    Based on your Profile inputs, GPAI obligations apply to this AI system because:
                </p>
                <div class="pl-8">
                     <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                        System is provided as or integrates a general-purpose AI (GPAI) model / component (Section 8, Q2)
                     </p>
                </div>
            </div>
        `;

        // Initial assessment confirmation
        html += `
            <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-3 px-4 shadow-sm flex items-center gap-2">
                 <p class="font-bold text-sm text-[#2E7D32]">✓ Confirmed</p>
            </div>
        `;

        // Provider determination
        html += `
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6 shadow-sm">
                <p class="font-bold text-sm text-[#22262A] mb-3">Provider Status</p>
                <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                    Please clarify your role in relation to the AI model:
                </p>
            </div>

            <div class="space-y-4 px-2 pt-2">
                <p class="font-bold text-sm text-[#22262A]">Are you the provider of the AI model (you develop it / release it under your name)? <span class="text-red-500">*</span></p>
                <div class="space-y-4 ml-2">
                    <label class="flex items-start gap-3 cursor-pointer group">
                        <input type="radio" name="gpai_provider_answer" value="Yes" 
                               ${block4State.gpaiProviderAnswer === 'Yes' ? 'checked' : ''}
                               onchange="setGPAIProviderAnswer('Yes')" 
                               class="w-4 h-4 text-[#F13D30] border-[#B5BCC4] focus:ring-[#F13D30] mt-0.5">
                        <span class="font-normal text-sm text-[#464E58] group-hover:text-[#111827]">Yes - I am the provider of the AI model</span>
                    </label>
                    <label class="flex items-start gap-3 cursor-pointer group">
                        <input type="radio" name="gpai_provider_answer" value="No" 
                               ${block4State.gpaiProviderAnswer === 'No' ? 'checked' : ''}
                               onchange="setGPAIProviderAnswer('No')" 
                               class="w-4 h-4 text-[#F13D30] border-[#B5BCC4] focus:ring-[#F13D30] mt-0.5">
                        <span class="font-normal text-sm text-[#464E58] group-hover:text-[#111827]">No - I am not the provider (e.g., I am a deployer / user of the model)</span>
                    </label>
                    <label class="flex items-start gap-3 cursor-pointer group">
                        <input type="radio" name="gpai_provider_answer" value="Not sure" 
                               ${block4State.gpaiProviderAnswer === 'Not sure' ? 'checked' : ''}
                               onchange="setGPAIProviderAnswer('Not sure')" 
                               class="w-4 h-4 text-[#F13D30] border-[#B5BCC4] focus:ring-[#F13D30] mt-0.5">
                        <span class="font-normal text-sm text-[#464E58] group-hover:text-[#111827]">Not sure - Requires further review</span>
                    </label>
                </div>
            </div>
        `;

        // Result banners
        if (status === 'Applies' && block4State.gpaiProviderAnswer === 'Yes') {
            html += `
                <div class="bg-[#FFF3E0] border border-[#FFB74D] rounded-lg p-6 shadow-sm mt-4">
                    <p class="font-bold text-sm text-[#E65100] mb-2">Result: GPAI Obligations Apply</p>
                    <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                        As the provider of the AI model, your AI system is subject to General-Purpose AI obligations under Chapter V of the EU AI Act.
                    </p>
                </div>
            `;
        } else if (status === 'Not Applicable' && block4State.gpaiProviderAnswer === 'No') {
            html += `
                <div class="bg-[#E8F5E9] border border-[#81C784] rounded-lg p-6 shadow-sm mt-4">
                    <p class="font-bold text-sm text-[#2E7D32] mb-2">Result: GPAI Obligations Not Applicable</p>
                    <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                        As you are not the provider of the AI model, GPAI obligations under Chapter V do not apply to you. However, you may have other obligations as a deployer or user.
                    </p>
                </div>
            `;
        } else if (status === 'Needs Review' && block4State.gpaiProviderAnswer === 'Not sure') {
            html += `
                <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-6 shadow-sm mt-4">
                    <p class="font-bold text-sm text-[#F57C00] mb-2">Result: Needs Review</p>
                    <p class="font-normal text-sm text-[#464E58] leading-relaxed">
                        Your provider status needs to be clarified. Please consult with your legal team or compliance officer to determine whether you are the provider of the AI model.
                    </p>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }
    
    return '<p class="text-sm text-[#464E58]">Status: ' + status + '</p>';
}

// Provider determination question
function renderBlock4ProviderQuestion(block4Details) {
    const gpaiIntegration = block4Details?.gpai_integration || 'Yes';
    
    return `
        <div class="space-y-4">
            <div class="bg-[#FFF9E6] border border-[#FFE59E] rounded-lg p-4">
                <p class="font-semibold text-sm text-[#22262A] mb-2">Provider Determination</p>
                <p class="font-normal text-sm text-[#464E58] mb-4">
                    Are you the provider of the AI model?
                </p>
                <div class="space-y-2">
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input type="radio" name="gpai_provider_answer" value="Yes" 
                               ${block4State.gpaiProviderAnswer === 'Yes' ? 'checked' : ''}
                               onchange="setGPAIProviderAnswer('Yes')" 
                               class="w-4 h-4 text-[#F13D30] border-[#B5BCC4] focus:ring-[#F13D30]">
                        <span class="font-normal text-sm text-[#464E58]">Yes - We are a GPAI provider</span>
                    </label>
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input type="radio" name="gpai_provider_answer" value="No" 
                               ${block4State.gpaiProviderAnswer === 'No' ? 'checked' : ''}
                               onchange="setGPAIProviderAnswer('No')" 
                               class="w-4 h-4 text-[#F13D30] border-[#B5BCC4] focus:ring-[#F13D30]">
                        <span class="font-normal text-sm text-[#464E58]">No - We only use/integrate GPAI from third parties</span>
                    </label>
                    <label class="flex items-center space-x-2 cursor-pointer">
                        <input type="radio" name="gpai_provider_answer" value="Not sure" 
                               ${block4State.gpaiProviderAnswer === 'Not sure' ? 'checked' : ''}
                               onchange="setGPAIProviderAnswer('Not sure')" 
                               class="w-4 h-4 text-[#F13D30] border-[#B5BCC4] focus:ring-[#F13D30]">
                        <span class="font-normal text-sm text-[#464E58]">Not sure - Requires legal review</span>
                    </label>
                </div>
            </div>
        </div>
    `;
}

// Block 4 API functions
async function confirmGPAI() {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block4-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                gpai_confirmed: true
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block4State.gpaiConfirmed = true;
            if (result.assessment && result.assessment.block4) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(4);
            }
        } else {
            alert('Error confirming assessment: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error confirming GPAI:', error);
        alert('Error confirming assessment. Please try again.');
    }
}

async function setGPAIProviderAnswer(value) {
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    try {
        const response = await fetch(`/api/ai-inventory/${agentId}/block4-state/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                gpai_provider_answer: value
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            block4State.gpaiProviderAnswer = value;
            if (result.assessment && result.assessment.block4) {
                updateAssessmentBlocksFromBE(result.assessment);
            } else {
                updateAssessmentBlock(4);
            }
        }
    } catch (error) {
        console.error('Error setting GPAI provider answer:', error);
    }
}



// Update all assessment blocks when switching to Assessment tab
function updateAllAssessmentBlocks() {
    // Try to get assessment results from BE first
    const mainContainer = document.querySelector('[data-agent-id]');
    const agentId = mainContainer ? parseInt(mainContainer.getAttribute('data-agent-id')) : 0;
    
    if (agentId) {
        // Load assessment from BE
        fetch(`/api/ai-inventory/${agentId}/detail/`)
            .then(response => response.json())
            .then(result => {
                if (result.success && result.data && result.data.assessment) {
                    console.log('Loading assessment from BE:', result.data.assessment);
                    updateAssessmentBlocksFromBE(result.data.assessment);
                } else {
                    // Fallback to client-side calculation if no BE data
                    [1, 2, 3, 4].forEach(blockNum => {
                        updateAssessmentBlock(blockNum);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading assessment from BE:', error);
                // Fallback to client-side calculation
                [1, 2, 3, 4].forEach(blockNum => {
                    updateAssessmentBlock(blockNum);
                });
            });
    } else {
        // Fallback to client-side calculation
        [1, 2, 3, 4].forEach(blockNum => {
            updateAssessmentBlock(blockNum);
        });
    }
}

// Update assessment blocks from BE results
function updateAssessmentBlocksFromBE(assessmentResults) {
    // Update Block 1
    if (assessmentResults.block1) {
        const block1Status = assessmentResults.block1.status;
        
        // Sync state from backend
        const backendHasState = assessmentResults.block1_state && Object.keys(assessmentResults.block1_state).length > 0;
        
        if (!backendHasState) {
            // Fresh assessment from profile save - RESET all frontend state
            block1State.prohibitedConfirmed = false;
            block1State.claimingException = '';
            block1State.exceptionQualifies = '';
            block1State.exceptionQualifiesMap = {};
            block1State.exceptionEvidenceMap = {};
            block1State.exceptionEvidenceUploaded = false;
            block1State.exceptionEvidenceSavedLink = '';
            block1State.exceptionEvidenceFiles = [];
            block1State.noExceptionConfirmed = false;
        } else {
            // SYNC frontend state from backend state
            const beState = assessmentResults.block1_state;
            block1State.prohibitedConfirmed = beState.prohibited_confirmed || false;
            block1State.claimingException = beState.claiming_exception || '';
            block1State.exceptionQualifies = beState.exception_qualifies || '';
            block1State.exceptionQualifiesMap = beState.exception_qualifies_map || {};
            block1State.exceptionEvidenceMap = beState.exception_evidence_map || {};
            block1State.exceptionEvidenceUploaded = beState.exception_evidence_uploaded || false;
            block1State.exceptionEvidenceSavedLink = beState.exception_evidence_saved_link || '';
            block1State.exceptionEvidenceFiles = beState.exception_evidence_files || [];
            block1State.noExceptionConfirmed = beState.no_exception_confirmed || false;
        }
        
        // Store BE assessment data for reference (needed for renderBlock1Content)
        block1State.be_assessment = assessmentResults.block1;
        
        const block1Content = renderBlock1Content(block1Status);
        updateBlockStatus(1, block1Status, block1Content);
    }
    
    // Update Block 2
    if (assessmentResults.block2) {
        const block2Status = assessmentResults.block2.status;
        const block2Details = assessmentResults.block2.details || {};
        
        // Sync state from backend
        const backendHasState = assessmentResults.block2_state && Object.keys(assessmentResults.block2_state).length > 0;
        if (!backendHasState) {
            block2State.highRiskConfirmed = false;
            block2State.uiConfirmedInSession = false;
            block2State.materialInfluence = '';
            block2State.narrowTasks = [];
            block2State.profiling = '';
            block2State.exemptionEvidenceUploaded = false;
            block2State.exemptionEvidenceSavedLink = '';
        } else {
            const beState = assessmentResults.block2_state;
            block2State.highRiskConfirmed = beState.high_risk_confirmed || false;
            block2State.materialInfluence = beState.material_influence || '';
            block2State.narrowTasks = beState.narrow_tasks || [];
            block2State.profiling = beState.profiling || '';
            block2State.exemptionEvidenceUploaded = beState.exemption_evidence_uploaded || false;
            block2State.exemptionEvidenceSavedLink = beState.exemption_evidence_saved_link || '';
        }

        // Store BE assessment data for reference
        block2State.be_assessment = assessmentResults.block2;
        
        const block2Content = renderBlock2Content(block2Status, block2Details);
        updateBlockStatus(2, block2Status, block2Content);
    }
    
    // Update Block 3
    if (assessmentResults.block3) {
        const block3Status = assessmentResults.block3.status;
        const block3Details = assessmentResults.block3.details || {};
        
        // Sync state from backend
        const backendHasState = assessmentResults.block3_state && Object.keys(assessmentResults.block3_state).length > 0;
        if (!backendHasState) {
            block3State.transparencyConfirmed = false;
            block3State.exceptionOptions = [];
            block3State.transparencyEvidenceUploaded = false;
            block3State.transparencyEvidenceSavedLink = '';
        } else {
            const beState = assessmentResults.block3_state;
            block3State.transparencyConfirmed = beState.transparency_confirmed || false;
            block3State.exceptionOptions = beState.exception_options || [];
            block3State.transparencyEvidenceUploaded = beState.transparency_evidence_uploaded || false;
            block3State.transparencyEvidenceSavedLink = beState.transparency_evidence_saved_link || '';
        }

        // Store BE assessment data for reference
        block3State.be_assessment = assessmentResults.block3;
        
        const block3Content = renderBlock3Content(block3Status, block3Details);
        updateBlockStatus(3, block3Status, block3Content);
    }
    
    // Update Block 4
    if (assessmentResults.block4) {
        const block4Status = assessmentResults.block4.status;
        const block4Details = assessmentResults.block4.details || {};
        
        // Sync state from backend
        const backendHasState = assessmentResults.block4_state && Object.keys(assessmentResults.block4_state).length > 0;
        if (!backendHasState) {
            block4State.gpaiConfirmed = false;
            block4State.gpaiProviderAnswer = '';
        } else {
            const beState = assessmentResults.block4_state;
            block4State.gpaiConfirmed = beState.gpai_confirmed || false;
            block4State.gpaiProviderAnswer = beState.gpai_provider_answer || '';
        }
        
        // Store BE assessment data for reference
        block4State.be_assessment = assessmentResults.block4;
        
        const block4Content = renderBlock4Content(block4Status, block4Details);
        updateBlockStatus(4, block4Status, block4Content);
    }
}


// Helper function to update block status and content
function updateBlockStatus(blockNum, status, content) {
    const statusEl = document.getElementById(`block-${blockNum}-status`);
    const contentEl = document.getElementById(`block-${blockNum}-content-inner`);
    
    if (statusEl) {
        let displayStatus = status;
        if (blockNum === 2 && status === 'Triggered') {
            displayStatus = 'High-risk';
        }
        statusEl.textContent = displayStatus;
        statusEl.className = `px-4 py-1.5 rounded-full font-semibold text-sm ${getStatusColorClass(status)}`;
    }
    
    if (contentEl) {
        contentEl.innerHTML = content;
    }
}

// Result screen status helpers
function getBlock1ResultStatus() {
    const status = getProhibitedStatus();
    if (status === 'PASS') return 'Not Prohibited';
    if (status === 'Triggered') return 'Needs Review';
    return status; // Returns 'Prohibited', 'Exception claimed', 'Needs Review', etc.
}

function getBlock2ResultStatus() {
    const status = getHighRiskStatus();
    if (status === 'Triggered') return 'Needs Review';
    return status; 
}

function getBlock3ResultStatus() {
    const status = getTransparencyStatus();
    if (status === 'Triggered') return 'Needs Review';
    return status;
}

function getBlock4ResultStatus() {
    return getGPAIStatus();
}

// Update all result blocks when switching to Result tab
function updateAllResultBlocks() {
    // Recheck all assessment blocks first to get latest status from Profile
    updateAllAssessmentBlocks();
    
    // Get result status using wrapper functions (which read from Profile and Assessment)
    const block1Result = getBlock1ResultStatus();
    const block2Result = getBlock2ResultStatus();
    const block3Result = getBlock3ResultStatus();
    const block4Result = getBlock4ResultStatus();
    
    // Map to result display format with descriptions
    const resultStatuses = [
        mapResultStatusToDisplay(block1Result, 1),
        mapResultStatusToDisplay(block2Result, 2),
        mapResultStatusToDisplay(block3Result, 3),
        mapResultStatusToDisplay(block4Result, 4)
    ];
    
    // Update each result block
    resultStatuses.forEach((result, index) => {
        updateResultBlock(index + 1, result.status, result.description, result.statusClass);
    });
}

// Result status display formatting
function mapResultStatusToDisplay(resultStatus, blockNum) {
    let description = '';
    let statusClass = '';
    
    switch(blockNum) {
        case 1: // Prohibited Practices
            if (resultStatus === 'Prohibited') {
                description = 'This AI system is classified as prohibited under Article 5 of the EU AI Act. It cannot be deployed or used within the EU.';
                statusClass = 'bg-[#FEEDEC] text-[#DC180A]';
            } else if (resultStatus === 'Not Prohibited' || resultStatus === 'PASS') {
                description = 'This AI system does not fall under prohibited practices. It may proceed to further compliance assessment.';
                statusClass = 'bg-[#E8F5E9] text-[#2E7D32]';
            } else if (resultStatus === 'Exception claimed' || resultStatus === 'Exception Claimed') {
                description = 'Your exception claim has been recorded with supporting evidence. This will be subject to regulatory review.';
                statusClass = 'bg-[#E8F5E9] text-[#2E7D32]';
            } else {
                description = 'This AI system requires further review to determine if it constitutes a prohibited practice. Consult with your legal team.';
                statusClass = 'bg-[#FFF9E6] text-[#F57C00]';
            }
            break;
            
        case 2: // High-Risk Classification
            if (resultStatus === 'De-activated') {
                description = 'This assessment is de-activated because the AI system is prohibited.';
                statusClass = 'bg-[#F0F1F2] text-[#B5BCC4]';
            } else if (resultStatus === 'High-Risk') {
                description = 'This AI system is classified as high-risk under Annex III of the EU AI Act. It must comply with strict requirements including risk management, data governance, and conformity assessment.';
                statusClass = 'bg-[#FFF3E0] text-[#E65100]';
            } else if (resultStatus === 'Not High-Risk') {
                description = 'This AI system is not classified as high-risk. It may still be subject to other obligations such as transparency requirements.';
                statusClass = 'bg-[#E8F5E9] text-[#2E7D32]';
            } else {
                description = 'This AI system requires further review to determine its high-risk classification. Additional information or clarification is needed.';
                statusClass = 'bg-[#FFF9E6] text-[#F57C00]';
            }
            break;
            
        case 3: // Transparency Obligation
            if (resultStatus === 'De-activated') {
                description = 'This assessment is de-activated because the AI system is prohibited.';
                statusClass = 'bg-[#F0F1F2] text-[#B5BCC4]';
            } else if (resultStatus === 'Applies') {
                description = 'This AI system is subject to transparency obligations under Article 50 of the EU AI Act. Users must be informed that they are interacting with AI.';
                statusClass = 'bg-[#FFF3E0] text-[#E65100]';
            } else if (resultStatus === 'Not Applicable') {
                description = 'This AI system is not subject to transparency obligations under Article 50, either because it does not trigger the requirements or valid exceptions apply.';
                statusClass = 'bg-[#E8F5E9] text-[#2E7D32]';
            } else {
                description = 'The transparency obligation status requires further review. Additional clarification or documentation may be needed.';
                statusClass = 'bg-[#FFF9E6] text-[#F57C00]';
            }
            break;
            
        case 4: // GPAI Applicability
            if (resultStatus === 'De-activated') {
                description = 'This assessment is de-activated because the AI system is prohibited.';
                statusClass = 'bg-[#F0F1F2] text-[#B5BCC4]';
            } else if (resultStatus === 'Applies') {
                description = 'This AI system is subject to General-Purpose AI obligations under Chapter V of the EU AI Act.';
                statusClass = 'bg-[#FFF3E0] text-[#E65100]';
            } else if (resultStatus === 'Not Applicable') {
                description = 'Based on your Profile inputs, this AI system does not qualify as a general-purpose AI model, so GPAI obligations under Chapter V of the EU AI Act do not apply.';
                statusClass = 'bg-[#E8F5E9] text-[#2E7D32]';
            } else if (resultStatus === 'Triggered') {
                description = 'Based on your Profile inputs, GPAI obligations may apply. Please confirm the assessment.';
                statusClass = 'bg-[#FFF3E0] text-[#E65100]';
            } else {
                description = 'GPAI integration status is Unknown or needs clarification to determine applicability. Consult with your technical team or legal counsel.';
                statusClass = 'bg-[#FFF9E6] text-[#F57C00]';
            }
            break;
    }
    
    return {
        status: resultStatus,
        description: description,
        statusClass: statusClass
    };
}

// Update a single result block
function updateResultBlock(blockNum, status, description, statusClass) {
    const blockElement = document.querySelector(`.result-block[data-block-id="${blockNum}"]`);
    if (!blockElement) return;
    
    const statusElement = blockElement.querySelector('.result-block-status');
    const descriptionElement = blockElement.querySelector('.result-block-description');
    
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `result-block-status px-3 py-1 text-sm font-medium rounded-full ${statusClass}`;
    }
    
    if (descriptionElement) {
        descriptionElement.textContent = description;
    }
}


// Update assessment when Profile inputs change
// Load detail data when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load AI System detail data from API
    loadAISystemDetailData();
    
    // Monitor Profile form changes
    const profileInputs = document.querySelectorAll('input[name="capability_practices"], input[name="sector_domain"], input[name="safety_component"], input[name="third_party_conformity"], input[name="interacts_persons"], input[name="synthetic_content"], input[name="affected_outputs"], input[name="deployment_context"], input[name="gpai_integration"]');
    profileInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (document.getElementById('content-assessment') && !document.getElementById('content-assessment').classList.contains('hidden')) {
                updateAllAssessmentBlocks();
            }
        });
    });
    
    // Handle "Same as compliance owner" checkbox
    document.getElementById('same-as-compliance-owner')?.addEventListener('change', function(e) {
        const ownerFields = document.querySelectorAll('input[name="owner_name"], input[name="owner_email"], input[name="owner_department"]');
        ownerFields.forEach(field => {
            field.disabled = e.target.checked;
            if (e.target.checked) {
                field.value = '';
            }
        });
    });
    
    // Handle "Part of broader product" radio
    document.querySelectorAll('input[name="part_of_product"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const productNameField = document.getElementById('product-service-name-field');
            if (this.value === 'yes') {
                productNameField?.classList.remove('hidden');
            } else {
                productNameField?.classList.add('hidden');
            }
        });
    });
    
    // Q1: Default Role Applies Logic
    initDefaultRoleLogic();
    
    // Q3: System Source Logic
    initSystemSourceLogic();
    
    // Q4: Modify/Customize Logic
    initModifyCustomizeLogic();
    
    // Q5 & Q6: EU/EEA Logic
    initEuEeaLogic();
    
    // Q3: Safety Component Logic (Section 8)
    initSafetyComponentLogic();
    
    // Other options with conditional text inputs
    initOtherOptionsLogic();
    
    // Q2: GPAI Integration Logic (Section 9)
    initGPAIIntegrationLogic();
    
    // Date Picker Implementation
    initDatePicker();
});

// Default Role Logic Functions
function initDefaultRoleLogic() {
    const defaultRoleYes = document.getElementById('default-role-yes');
    const defaultRoleNo = document.getElementById('default-role-no');
    const roleCheckboxes = document.querySelectorAll('.role-checkbox');
    const orgDefaultRoles = JSON.parse('{{ org_default_roles_json|escapejs|default:"[]" }}');
    
    // Map role names to checkbox IDs
    const roleIdMap = {
        'Provider': 'role-provider',
        'Deployer': 'role-deployer',
        'Importer': 'role-importer',
        'Distributor': 'role-distributor'
    };
    
    function handleDefaultRoleChange(value) {
        if (value === 'Yes') {
            // Disable all role checkboxes
            roleCheckboxes.forEach(checkbox => {
                checkbox.disabled = true;
                const label = checkbox.closest('label');
                if (label) {
                    label.classList.remove('hover:bg-[#F9FAFB]', 'cursor-pointer');
                    label.classList.add('opacity-60', 'cursor-not-allowed');
                }
            });
            
            // Auto-check all default roles from Organization (multiple roles)
            const rolesToCheck = Array.isArray(orgDefaultRoles) && orgDefaultRoles.length ? orgDefaultRoles : ['Deployer'];
            rolesToCheck.forEach(function(roleName) {
                const defaultRoleId = roleIdMap[roleName];
                if (defaultRoleId) {
                    const defaultRoleCheckbox = document.getElementById(defaultRoleId);
                    if (defaultRoleCheckbox) {
                        defaultRoleCheckbox.checked = true;
                        const label = defaultRoleCheckbox.closest('label');
                        if (label) {
                            label.classList.add('border-[#F13D30]', 'bg-[#FEEDEC]');
                        }
                    }
                }
            });
        } else {
            // Enable all role checkboxes
            roleCheckboxes.forEach(checkbox => {
                checkbox.disabled = false;
                const label = checkbox.closest('label');
                if (label) {
                    label.classList.add('hover:bg-[#F9FAFB]', 'cursor-pointer');
                    label.classList.remove('opacity-60', 'cursor-not-allowed');
                }
            });
            
            // Clear all role selections
            roleCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
                const label = checkbox.closest('label');
                if (label) {
                    label.classList.remove('border-[#F13D30]', 'bg-[#FEEDEC]');
                }
            });
        }
    }
    
    // Add event listeners
    if (defaultRoleYes) {
        defaultRoleYes.addEventListener('change', function() {
            if (this.checked) {
                handleDefaultRoleChange('Yes');
            }
        });
    }
    
    if (defaultRoleNo) {
        defaultRoleNo.addEventListener('change', function() {
            if (this.checked) {
                handleDefaultRoleChange('No');
            }
        });
    }
    
    // Handle role checkbox changes (only when enabled)
    roleCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.disabled) return;
            
            const label = this.closest('label');
            if (this.checked) {
                if (label) {
                    label.classList.add('border-[#F13D30]', 'bg-[#FEEDEC]');
                }
            } else {
                if (label) {
                    label.classList.remove('border-[#F13D30]', 'bg-[#FEEDEC]');
                }
            }
        });
    });
    
    // Initialize state based on default selection
    if (defaultRoleNo && defaultRoleNo.checked) {
        handleDefaultRoleChange('No');
    }
}

// Date Picker Functions
let currentDate = new Date();
let selectedDate = null;

function initDatePicker() {
    const dateInput = document.getElementById('go-live-date-input');
    const dateHidden = document.getElementById('go-live-date-hidden');
    const datePicker = document.getElementById('date-picker-dropdown');
    
    if (!dateInput || !datePicker) return;
    
    // Format date as DD/MM/YYYY
    function formatDate(date) {
        if (!date) return '';
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }
    
    // Parse DD/MM/YYYY to Date
    function parseDate(dateStr) {
        if (!dateStr) return null;
        const parts = dateStr.split('/');
        if (parts.length !== 3) return null;
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1;
        const year = parseInt(parts[2], 10);
        return new Date(year, month, day);
    }
    
    // Update display input with formatted date and highlight day
    function updateDisplayInput(date) {
        const dayEl = document.getElementById('date-day');
        const monthEl = document.getElementById('date-month');
        const yearEl = document.getElementById('date-year');
        const wrapper = document.getElementById('go-live-date-wrapper');
        
        if (!date) {
            dateInput.value = '';
            if (dayEl) dayEl.textContent = 'DD';
            if (monthEl) monthEl.textContent = 'MM';
            if (yearEl) yearEl.textContent = 'YYYY';
            if (wrapper) wrapper.classList.remove('date-input-has-value');
            return;
        }
        
        const formatted = formatDate(date);
        dateInput.value = formatted;
        
        // Update display elements
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        if (dayEl) {
            dayEl.textContent = day;
            dayEl.classList.add('px-1.5', 'py-0.5', 'rounded', 'bg-[#3B82F6]/20', 'text-[#3B82F6]', 'font-medium');
        }
        if (monthEl) monthEl.textContent = month;
        if (yearEl) yearEl.textContent = year;
        if (wrapper) wrapper.classList.add('date-input-has-value');
        
        // Update hidden input for form submission
        if (dateHidden) {
            const isoDate = date.toISOString().split('T')[0];
            dateHidden.value = isoDate;
        }
    }
    
    // Render calendar
    function renderCalendar() {
        const calendarEl = document.getElementById('date-picker-calendar');
        const monthYearEl = document.getElementById('date-picker-month-year');
        if (!calendarEl || !monthYearEl) return;
        
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        
        // Update month/year display
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        monthYearEl.textContent = `${monthNames[month]} ${year}`;
        
        // Get first day of month and number of days
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startingDayOfWeek = (firstDay.getDay() + 6) % 7; // Monday = 0
        
        // Get today's date
        const today = new Date();
        const isToday = (date) => {
            return date.getDate() === today.getDate() &&
                   date.getMonth() === today.getMonth() &&
                   date.getFullYear() === today.getFullYear();
        };
        
        // Get previous month's last days
        const prevMonth = new Date(year, month, 0);
        const prevMonthDays = prevMonth.getDate();
        
        calendarEl.innerHTML = '';
        
        // Previous month days
        for (let i = startingDayOfWeek - 1; i >= 0; i--) {
            const day = prevMonthDays - i;
            const date = new Date(year, month - 1, day);
            const dayEl = document.createElement('button');
            dayEl.type = 'button';
            dayEl.className = 'w-8 h-8 text-xs text-[#6B7280] hover:bg-white/10 rounded transition-colors';
            dayEl.textContent = day;
            dayEl.onclick = () => {
                currentDate = new Date(year, month - 1, day);
                renderCalendar();
            };
            calendarEl.appendChild(dayEl);
        }
        
        // Current month days
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const dayEl = document.createElement('button');
            dayEl.type = 'button';
            dayEl.className = 'w-8 h-8 text-xs text-white hover:bg-white/20 rounded transition-colors';
            
            // Check if selected
            const isSelected = selectedDate && 
                date.getDate() === selectedDate.getDate() &&
                date.getMonth() === selectedDate.getMonth() &&
                date.getFullYear() === selectedDate.getFullYear();
            
            // Check if today
            const isTodayDate = isToday(date);
            
            if (isSelected) {
                dayEl.className += ' bg-white/30 border border-[#F13D30]';
            } else if (isTodayDate) {
                dayEl.className += ' text-[#3B82F6] font-semibold';
            }
            
            dayEl.textContent = day;
            dayEl.onclick = () => {
                selectedDate = date;
                updateDisplayInput(date);
                datePicker.classList.add('hidden');
                const wrapper = document.getElementById('go-live-date-wrapper');
                if (wrapper) wrapper.classList.remove('border-[#F13D30]', 'ring-2', 'ring-[#FEEDEC]');
            };
            calendarEl.appendChild(dayEl);
        }
        
        // Next month days
        const totalCells = calendarEl.children.length;
        const remainingCells = 42 - totalCells; // 6 rows * 7 days
        for (let day = 1; day <= remainingCells; day++) {
            const date = new Date(year, month + 1, day);
            const dayEl = document.createElement('button');
            dayEl.type = 'button';
            dayEl.className = 'w-8 h-8 text-xs text-[#6B7280] hover:bg-white/10 rounded transition-colors';
            dayEl.textContent = day;
            dayEl.onclick = () => {
                currentDate = new Date(year, month + 1, day);
                renderCalendar();
            };
            calendarEl.appendChild(dayEl);
        }
    }
    
    // Toggle date picker - Click handler
    const dateWrapper = document.getElementById('go-live-date-wrapper');
    const dateDisplay = document.getElementById('go-live-date-display');
    
    function toggleDatePicker(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        const isHidden = datePicker.classList.contains('hidden');
        
        if (isHidden) {
            // Show calendar
            datePicker.classList.remove('hidden');
            if (dateWrapper) {
                dateWrapper.classList.add('border-[#F13D30]');
                dateWrapper.classList.add('ring-2', 'ring-[#FEEDEC]');
            }
            // Ensure calendar is rendered
            renderCalendar();
        } else {
            // Hide calendar
            datePicker.classList.add('hidden');
            if (dateWrapper) {
                dateWrapper.classList.remove('border-[#F13D30]', 'ring-2', 'ring-[#FEEDEC]');
            }
        }
    }
    
    // Add click listeners to wrapper and input
    if (dateWrapper) {
        dateWrapper.addEventListener('click', toggleDatePicker);
    }
    
    if (dateInput) {
        dateInput.addEventListener('click', toggleDatePicker);
        dateInput.addEventListener('focus', toggleDatePicker);
    }
    
    if (dateDisplay) {
        dateDisplay.addEventListener('click', toggleDatePicker);
    }
    
    // Close date picker when clicking outside
    document.addEventListener('click', function(e) {
        if (dateWrapper && !dateWrapper.contains(e.target) && !datePicker.contains(e.target)) {
            datePicker.classList.add('hidden');
            dateWrapper.classList.remove('border-[#F13D30]', 'ring-2', 'ring-[#FEEDEC]');
        }
    });
    
    // Navigation buttons
    document.getElementById('date-picker-prev-month')?.addEventListener('click', function(e) {
        e.stopPropagation();
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    
    document.getElementById('date-picker-next-month')?.addEventListener('click', function(e) {
        e.stopPropagation();
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    
    document.getElementById('date-picker-today')?.addEventListener('click', function(e) {
        e.stopPropagation();
        const today = new Date();
        currentDate = new Date(today);
        selectedDate = new Date(today);
        updateDisplayInput(today);
        renderCalendar();
    });
    
    // Initialize with today's date if no value
    if (!dateInput.value) {
        const today = new Date();
        selectedDate = new Date(today);
        currentDate = new Date(today);
        updateDisplayInput(today);
    } else {
        // Parse existing value
        const parsed = parseDate(dateInput.value);
        if (parsed) {
            selectedDate = parsed;
            currentDate = new Date(parsed);
        }
    }
    
    renderCalendar();
}

// System Source Logic Functions
function initSystemSourceLogic() {
    const systemSourceRadios = document.querySelectorAll('input[name="system_source"]');
    const vendorFields = document.getElementById('vendor-fields');
    const saveVendorLinkBtn = document.getElementById('save-vendor-link-btn');
    const vendorEvidenceLink = document.getElementById('vendor-evidence-link');
    const vendorLinkSaved = document.getElementById('vendor-link-saved');
    const vendorLinkText = document.getElementById('vendor-link-text');
    
    function handleSystemSourceChange() {
        const selectedValue = document.querySelector('input[name="system_source"]:checked')?.value;
        
        // Update styling for selected option
        document.querySelectorAll('.system-source-option').forEach(label => {
            const radio = label.querySelector('input[type="radio"]');
            if (radio && radio.checked) {
                label.classList.add('border-[#F13D30]', 'bg-[#FEEDEC]');
                label.classList.remove('border-[#F0F1F2]', 'bg-white');
            } else {
                label.classList.remove('border-[#F13D30]', 'bg-[#FEEDEC]');
                label.classList.add('border-[#F0F1F2]', 'bg-white');
            }
        });
        
        // Show/hide vendor fields
        if (selectedValue === 'Vendor / Third-party' || selectedValue === 'Mixed') {
            vendorFields?.classList.remove('hidden');
        } else {
            vendorFields?.classList.add('hidden');
        }
    }
    
    systemSourceRadios.forEach(radio => {
        radio.addEventListener('change', handleSystemSourceChange);
    });
    
    // Save vendor link handler
    if (saveVendorLinkBtn && vendorEvidenceLink) {
        saveVendorLinkBtn.addEventListener('click', function() {
            const link = vendorEvidenceLink.value.trim();
            if (link) {
                // Create clickable link element
                vendorLinkText.innerHTML = `<a href="${link}" target="_blank" class="text-[#F13D30] hover:underline">${link}</a>`;
                vendorLinkSaved.classList.remove('hidden');
                // Note: Link will be saved when user clicks "Confirm and Save" or "Save all"
            }
        });
    }
    
    // Trigger initial change to show/hide vendor fields based on saved data
    handleSystemSourceChange();
    
    // Initialize
    handleSystemSourceChange();
}

// Modify/Customize Logic Functions
function initModifyCustomizeLogic() {
    const modifyRadios = document.querySelectorAll('input[name="modify_customize"]');
    const modifyWarning = document.getElementById('modify-warning');
    
    function handleModifyChange() {
        const selectedValue = document.querySelector('input[name="modify_customize"]:checked')?.value;
        
        if (selectedValue === 'Yes') {
            modifyWarning?.classList.remove('hidden');
        } else {
            modifyWarning?.classList.add('hidden');
        }
    }
    
    modifyRadios.forEach(radio => {
        radio.addEventListener('change', handleModifyChange);
    });
    
    // Initialize
    handleModifyChange();
}

// EU/EEA Logic Functions
function initEuEeaLogic() {
    const euUsageRadios = document.querySelectorAll('input[name="eu_usage"]');
    const euEffectRadios = document.querySelectorAll('input[name="eu_effect"]');
    const euActNotice = document.getElementById('eu-act-notice');
    
    function updateEuUsageStyling() {
        document.querySelectorAll('.eu-usage-option').forEach(label => {
            const radio = label.querySelector('input[type="radio"]');
            if (radio && radio.checked) {
                label.classList.add('border-[#F13D30]', 'bg-[#FEEDEC]');
                label.classList.remove('border-[#F0F1F2]', 'bg-white');
            } else {
                label.classList.remove('border-[#F13D30]', 'bg-[#FEEDEC]');
                label.classList.add('border-[#F0F1F2]', 'bg-white');
            }
        });
    }
    
    function updateEuEffectStyling() {
        document.querySelectorAll('.eu-effect-option').forEach(label => {
            const radio = label.querySelector('input[type="radio"]');
            if (radio && radio.checked) {
                label.classList.add('border-[#F13D30]', 'bg-[#FEEDEC]');
                label.classList.remove('border-[#F0F1F2]', 'bg-white');
            } else {
                label.classList.remove('border-[#F13D30]', 'bg-[#FEEDEC]');
                label.classList.add('border-[#F0F1F2]', 'bg-white');
            }
        });
    }
    
    function checkEuActNotice() {
        const euUsage = document.querySelector('input[name="eu_usage"]:checked')?.value;
        const euEffect = document.querySelector('input[name="eu_effect"]:checked')?.value;
        
        if (euUsage === 'No' && euEffect === 'No') {
            euActNotice?.classList.remove('hidden');
        } else {
            euActNotice?.classList.add('hidden');
        }
    }
    
    euUsageRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            updateEuUsageStyling();
            checkEuActNotice();
        });
    });
    
    euEffectRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            updateEuEffectStyling();
            checkEuActNotice();
        });
    });
    
    // Initialize
    updateEuUsageStyling();
    updateEuEffectStyling();
    checkEuActNotice();
    // Expose so notice updates after loadProfileData sets eu_usage / eu_effect
    window.refreshEuActNotice = function() {
        updateEuUsageStyling();
        updateEuEffectStyling();
        checkEuActNotice();
    };
}

// Safety Component Logic Functions (Section 8, Q3)
function initSafetyComponentLogic() {
    const safetyComponentYes = document.getElementById('safety-component-yes');
    const safetyComponentNo = document.getElementById('safety-component-no');
    const thirdPartyConformityField = document.getElementById('third-party-conformity-field');
    const thirdPartyConformityRadios = document.querySelectorAll('input[name="third_party_conformity"]');
    
    function handleSafetyComponentChange() {
        const selectedValue = document.querySelector('input[name="safety_component"]:checked')?.value;
        
        if (selectedValue === 'Yes') {
            // Show follow-up question
            thirdPartyConformityField?.classList.remove('hidden');
        } else {
            // Hide follow-up question and clear selection
            thirdPartyConformityField?.classList.add('hidden');
            thirdPartyConformityRadios.forEach(radio => {
                radio.checked = false;
            });
        }
    }
    
    if (safetyComponentYes) {
        safetyComponentYes.addEventListener('change', handleSafetyComponentChange);
    }
    
    if (safetyComponentNo) {
        safetyComponentNo.addEventListener('change', handleSafetyComponentChange);
    }
    
    // Initialize state
    handleSafetyComponentChange();
}

// Other Options Logic Functions
function initOtherOptionsLogic() {
    // Section 4, Q2: Sector domains - Other / not listed
    const sectorOtherCheckbox = document.getElementById('sector-other-checkbox');
    const sectorOtherInput = document.getElementById('sector-other-input');
    
    if (sectorOtherCheckbox && sectorOtherInput) {
        sectorOtherCheckbox.addEventListener('change', function() {
            if (this.checked) {
                sectorOtherInput.classList.remove('hidden');
            } else {
                sectorOtherInput.classList.add('hidden');
                sectorOtherInput.value = '';
            }
        });
    }
    
    // Section 5, Q1: Deployment Context - Other
    const deploymentOtherRadio = document.getElementById('deployment-other-radio');
    const deploymentOtherInput = document.getElementById('deployment-other-input');
    const deploymentContextRadios = document.querySelectorAll('.deployment-context-radio');
    
    function handleDeploymentContextChange() {
        const selectedValue = document.querySelector('input[name="deployment_context"]:checked')?.value;
        if (selectedValue === 'Other') {
            deploymentOtherInput?.classList.remove('hidden');
        } else {
            deploymentOtherInput?.classList.add('hidden');
            if (deploymentOtherInput) deploymentOtherInput.value = '';
        }
    }
    
    deploymentContextRadios.forEach(radio => {
        radio.addEventListener('change', handleDeploymentContextChange);
    });
    
    // Section 5, Q2: System Users - Other
    const systemUsersOtherCheckbox = document.getElementById('system-users-other-checkbox');
    const systemUsersOtherInput = document.getElementById('system-users-other-input');
    
    if (systemUsersOtherCheckbox && systemUsersOtherInput) {
        systemUsersOtherCheckbox.addEventListener('change', function() {
            if (this.checked) {

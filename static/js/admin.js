// Pet data management
class PetDashboard {
    constructor() {
        this.pets = [];
        this.currentView = 'dashboard';
        this.currentType = null;
        this.init();
    }

    init() {
        this.loadPetData();
        this.setupEventListeners();
        this.updateCounts();
    }

    // Load pet data from localStorage or initialize with sample data
    loadPetData() {
        const savedPets = localStorage.getItem('petData');
        if (savedPets) {
            this.pets = JSON.parse(savedPets);
        } else {
            // Initialize with sample data for testing
            this.pets = [
                {
                    id: 1,
                    name: 'Buddy',
                    type: 'lost',
                    description: 'Golden Retriever, very friendly',
                    location: 'Central Park area',
                    contact: 'john@example.com',
                    status: 'pending',
                    dateReported: '2024-01-15'
                },
                {
                    id: 2,
                    name: 'Whiskers',
                    type: 'found',
                    description: 'Orange tabby cat with white chest',
                    location: 'Downtown library',
                    contact: 'mary@example.com',
                    status: 'pending',
                    dateReported: '2024-01-16'
                },
                {
                    id: 3,
                    name: 'Max',
                    type: 'adopt',
                    description: 'Young German Shepherd, house trained',
                    location: 'Animal Shelter',
                    contact: 'shelter@example.com',
                    status: 'pending',
                    dateReported: '2024-01-14'
                },
                {
                    id: 4,
                    name: 'Luna',
                    type: 'lost',
                    description: 'Small black and white Border Collie',
                    location: 'Riverside Park',
                    contact: 'sarah@example.com',
                    status: 'resolved',
                    dateReported: '2024-01-13'
                },
                {
                    id: 5,
                    name: 'Mittens',
                    type: 'adopt',
                    description: 'Friendly indoor cat, good with children',
                    location: 'Pet Rescue Center',
                    contact: 'rescue@example.com',
                    status: 'pending',
                    dateReported: '2024-01-17'
                }
            ];
            this.savePetData();
        }
    }

    // Save pet data to localStorage
    savePetData() {
        localStorage.setItem('petData', JSON.stringify(this.pets));
    }

    // Set up event listeners
    setupEventListeners() {
        // Action button listeners
        const actionButtons = document.querySelectorAll('.action-btn');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                this.showPetDetails(type);
            });
        });

        // Back button listener
        const backBtn = document.getElementById('back-btn');
        backBtn.addEventListener('click', () => {
            this.showDashboard();
        });
    }

    // Update count displays
    updateCounts() {
        const counts = {
            lost: this.pets.filter(pet => pet.type === 'lost' && pet.status === 'pending').length,
            found: this.pets.filter(pet => pet.type === 'found' && pet.status === 'pending').length,
            adopt: this.pets.filter(pet => pet.type === 'adopt' && pet.status === 'pending').length
        };

        document.getElementById('lost-count').textContent = counts.lost;
        document.getElementById('found-count').textContent = counts.found;
        document.getElementById('adopt-count').textContent = counts.adopt;
    }

    // Show dashboard view
    showDashboard() {
        document.getElementById('dashboard-view').classList.remove('hidden');
        document.getElementById('details-view').classList.add('hidden');
        this.currentView = 'dashboard';
        this.updateCounts();
    }

    // Show pet details view
    showPetDetails(type) {
        this.currentType = type;
        document.getElementById('dashboard-view').classList.add('hidden');
        document.getElementById('details-view').classList.remove('hidden');
        this.currentView = 'details';

        // Update title
        const title = document.getElementById('details-title');
        title.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Pet Requests`;

        // Render pet list
        this.renderPetList(type);
    }

    // Render pet list for specific type
    renderPetList(type) {
        const petList = document.getElementById('pet-list');
        const filteredPets = this.pets.filter(pet => pet.type === type);

        if (filteredPets.length === 0) {
            petList.innerHTML = `
                <div class="pet-item">
                    <p>No ${type} pet requests found.</p>
                </div>
            `;
            return;
        }

        petList.innerHTML = filteredPets.map(pet => this.createPetItemHTML(pet)).join('');

        // Add event listeners for status buttons
        const statusButtons = petList.querySelectorAll('.status-btn');
        statusButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const petId = parseInt(e.target.dataset.petId);
                this.updatePetStatus(petId);
            });
        });
    }

    // Create HTML for pet item
    createPetItemHTML(pet) {
        const statusClass = pet.status === 'pending' ? 'status-pending' : 'status-resolved';
        const buttonText = pet.status === 'pending' ? 'Mark as Resolved' : 'Resolved';
        const buttonDisabled = pet.status === 'resolved' ? 'disabled' : '';

        return `
            <div class="pet-item">
                <div class="pet-header">
                    <div class="pet-info">
                        <h3>${pet.name}</h3>
                        <p><strong>Description:</strong> ${pet.description}</p>
                        <p><strong>Location:</strong> ${pet.location}</p>
                        <p><strong>Contact:</strong> ${pet.contact}</p>
                        <p><strong>Date Reported:</strong> ${pet.dateReported}</p>
                    </div>
                    <div class="status-controls">
                        <span class="status-badge ${statusClass}">${pet.status}</span>
                        <button class="status-btn" data-pet-id="${pet.id}" ${buttonDisabled}>
                            ${buttonText}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Update pet status
    updatePetStatus(petId) {
        const petIndex = this.pets.findIndex(pet => pet.id === petId);
        if (petIndex !== -1) {
            this.pets[petIndex].status = 'resolved';
            this.savePetData();
            
            // Refresh the current view
            if (this.currentView === 'details') {
                this.renderPetList(this.currentType);
            }
            this.updateCounts();
        }
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PetDashboard();
});
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.action-btn');
    const dashboardView = document.getElementById('dashboard-view');
    const detailsView = document.getElementById('details-view');
    const petList = document.getElementById('pet-list');
    const backBtn = document.getElementById('back-btn');
    const detailsTitle = document.getElementById('details-title');

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const type = button.dataset.type;
            detailsTitle.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Pets`;

            fetch(`/admin/get_pets/${type}`)
                .then(response => response.json())
                .then(data => {
                    petList.innerHTML = '';
                    if (data.length === 0) {
                        petList.innerHTML = '<p>No pets available.</p>';
                        return;
                    }

                    data.forEach(pet => {
                        const card = document.createElement('div');
                        card.classList.add('pet-card');
                        card.innerHTML = `
                            <img src="/static/uploads/${pet.image}" alt="${pet.name}">
                            <h3>${pet.name}</h3>
                            <p><strong>Breed:</strong> ${pet.breed}</p>
                            <p>${pet.description}</p>
                            <div class="pet-actions">
                                <button onclick="editPet(${pet.id})">Edit</button>
                                <button onclick="deletePet(${pet.id})">Delete</button>
                            </div>
                        `;
                        petList.appendChild(card);
                    });
                });

            dashboardView.classList.add('hidden');
            detailsView.classList.remove('hidden');
        });
    });

    backBtn.addEventListener('click', () => {
        detailsView.classList.add('hidden');
        dashboardView.classList.remove('hidden');
    });
});

function deletePet(id) {
    if (confirm("Are you sure you want to delete this pet?")) {
        fetch(`/admin/delete_pet/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                location.reload();
            });
    }
}

function editPet(id) {
    window.location.href = `/admin/edit_pet/${id}`;
}

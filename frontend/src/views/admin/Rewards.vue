<template>
  <div>
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h2>🛒 Item Catalog</h2>
        <p>Manage the guild's item offerings</p>
      </div>
      <button class="btn btn-primary" @click="openModal()">
        ➕ Add Item
      </button>
    </div>

    <!-- Rewards Grid -->
    <div class="grid-container">
      <div v-for="reward in rewards" :key="reward.id" class="card reward-card">
        <div class="reward-image">
            <img v-if="reward.image" :src="reward.image" :alt="reward.name" />
            <div v-else class="placeholder">🎁</div>
        </div>
        <div class="reward-content">
            <h3>{{ reward.name }}</h3>
            <p>{{ reward.description }}</p>
            <div class="reward-cost">
                <span>{{ reward.point_cost }} 💰 gold</span>
            </div>
            <div class="reward-actions">
                <button class="btn btn-secondary btn-sm" @click="openModal(reward)">Edit</button>
                <button class="btn btn-danger btn-sm" @click="confirmDelete(reward)">Delete</button>
            </div>
        </div>
      </div>
    </div>
    
    <div v-if="rewards.length === 0" class="empty-state card">
        <h3>No items in catalog</h3>
        <p>Create your first item to get started.</p>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content">
        <h3>{{ isEditing ? 'Edit Item' : 'Add Item' }}</h3>
        
        <div class="form-group">
            <label>Name</label>
            <input v-model="form.name" class="form-input" placeholder="e.g. Healing Potion" />
        </div>
        
        <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" class="form-input" placeholder="Item description..."></textarea>
        </div>
        
        <div class="form-group">
            <label>Cost (Gold)</label>
            <input v-model.number="form.point_cost" type="number" class="form-input" placeholder="e.g. 100" />
        </div>
        
        <div class="form-group">
            <label>Item Image</label>
            <div class="image-upload-area">
              <div v-if="imagePreview || form.image" class="image-preview">
                <img :src="imagePreview || form.image" alt="Preview" />
                <button class="remove-image" @click="removeImage">✕</button>
              </div>
              <label v-else class="upload-label">
                <span class="upload-icon">📷</span>
                <span>Click to upload image</span>
                <input type="file" accept="image/*" @change="handleImageSelect" class="hidden-input" />
              </label>
            </div>
        </div>

        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
            <button class="btn btn-secondary" @click="showModal = false">Cancel</button>
            <button class="btn btn-primary" @click="saveReward" :disabled="!form.name || !form.point_cost || saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getRewards, createReward, updateReward, deleteReward, uploadRewardImage } from '../../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      rewards: [],
      showModal: false,
      isEditing: false,
      saving: false,
      pendingImageFile: null,
      imagePreview: null,
      form: {
        id: null,
        name: '',
        description: '',
        point_cost: null,
        image: ''
      }
    }
  },
  async mounted() {
    await this.loadRewards()
  },
  methods: {
    async loadRewards() {
      try {
        const { data } = await getRewards()
        this.rewards = data
      } catch (e) {
        console.error(e)
      }
    },
    openModal(reward = null) {
        this.pendingImageFile = null
        this.imagePreview = null
        if (reward) {
            this.isEditing = true
            this.form = { ...reward }
        } else {
            this.isEditing = false
            this.form = { id: null, name: '', description: '', point_cost: null, image: '' }
        }
        this.showModal = true
    },
    handleImageSelect(event) {
        const file = event.target.files[0]
        if (!file) return
        this.pendingImageFile = file
        this.imagePreview = URL.createObjectURL(file)
    },
    removeImage() {
        this.pendingImageFile = null
        this.imagePreview = null
        this.form.image = ''
    },
    async saveReward() {
        this.saving = true
        try {
            let rewardId
            if (this.isEditing) {
                await updateReward(this.form.id, this.form)
                rewardId = this.form.id
                this.showToast('Item updated ⚔️')
            } else {
                const { data } = await createReward(this.form)
                rewardId = data.id
                this.showToast('Item created ⚔️')
            }

            // Upload image if a file was selected
            if (this.pendingImageFile && rewardId) {
                const formData = new FormData()
                formData.append('file', this.pendingImageFile)
                await uploadRewardImage(rewardId, formData)
            }

            this.showModal = false
            await this.loadRewards()
        } catch (e) {
            this.showToast('Failed to save item', 'error')
        } finally {
            this.saving = false
        }
    },
    async confirmDelete(reward) {
        if (confirm(`Delete ${reward.name}?`)) {
            try {
                await deleteReward(reward.id)
                this.showToast('Item removed from catalog')
                await this.loadRewards()
            } catch (e) {
                this.showToast('Failed to delete', 'error')
            }
        }
    }
  }
}
</script>

<style scoped>
.grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 24px;
    margin-top: 20px;
}

.reward-card {
    overflow: hidden;
    padding: 0 !important;
    display: flex;
    flex-direction: column;
    border-radius: 12px !important;
    border: 2px solid rgba(212,164,76,0.15) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.reward-card:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 32px rgba(212,164,76,0.1) !important;
    border-color: rgba(212,164,76,0.3) !important;
}

.reward-image {
    height: 160px;
    background: linear-gradient(135deg, rgba(44,24,16,0.6), rgba(26,26,46,0.8));
    display: flex;
    align-items: center;
    justify-content: center;
}

.reward-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.reward-image .placeholder {
    font-size: 56px;
}

.reward-content {
    padding: 20px;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.reward-content h3 {
    margin: 0 0 8px 0;
    color: #e8d5b7;
    font-weight: 700;
    font-family: 'Cinzel', serif;
}

.reward-content p {
    font-size: 14px;
    color: #8b7355;
    margin-bottom: 12px;
    flex: 1;
    font-weight: 500;
}

.reward-cost {
    font-weight: 800;
    font-size: 18px;
    color: #d4a44c;
    margin-bottom: 16px;
}

.reward-actions {
    display: flex;
    gap: 8px;
}

/* Image upload area */
.image-upload-area {
    border: 2px dashed rgba(212,164,76,0.2);
    border-radius: 12px;
    overflow: hidden;
    transition: border-color 0.2s;
}
.image-upload-area:hover {
    border-color: rgba(212,164,76,0.4);
}
.upload-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 24px;
    cursor: pointer;
    color: #8b7355;
    font-weight: 600;
    font-size: 13px;
}
.upload-icon { font-size: 28px; }
.hidden-input { display: none; }
.image-preview {
    position: relative;
    height: 140px;
}
.image-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 10px;
}
.remove-image {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: rgba(0,0,0,0.5);
    color: white;
    border: none;
    cursor: pointer;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>

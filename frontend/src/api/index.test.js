import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as api from '@/api'
import request from '@/utils/request'

// Mock the request module
vi.mock('@/utils/request', () => ({
  default: Object.assign(
    vi.fn(), // For direct function calls like request({...})
    {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    }
  )
}))

describe('API modules', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('authAPI', () => {
    describe('login', () => {
      it('should call request.post with correct parameters', () => {
        const loginData = { username: 'test', password: 'pass' }

        api.authAPI.login(loginData)

        expect(request.post).toHaveBeenCalledWith('/login', loginData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        })
      })
    })

    describe('changePassword', () => {
      it('should call request.post with correct parameters', () => {
        const passwordData = {
          old_password: 'old',
          new_password: 'new'
        }

        api.authAPI.changePassword(passwordData)

        expect(request.post).toHaveBeenCalledWith('/change-password', passwordData)
      })
    })
  })

  describe('peerAPI', () => {
    describe('getPeers', () => {
      it('should call request.get with correct endpoint', () => {
        api.peerAPI.getPeers()

        expect(request.get).toHaveBeenCalledWith('/peers')
      })
    })

    describe('createPeer', () => {
      it('should call request.post with correct parameters', () => {
        const peerData = { name: 'test-peer', ip: '10.0.0.1' }

        api.peerAPI.createPeer(peerData)

        expect(request.post).toHaveBeenCalledWith('/peers', peerData)
      })
    })

    describe('updatePeer', () => {
      it('should call request.put with correct parameters', () => {
        const peerId = 1
        const peerData = { name: 'updated-peer' }

        api.peerAPI.updatePeer(peerId, peerData)

        expect(request.put).toHaveBeenCalledWith('/peers/1', peerData)
      })
    })

    describe('deletePeer', () => {
      it('should call request.delete with correct endpoint', () => {
        const peerId = 1

        api.peerAPI.deletePeer(peerId)

        expect(request.delete).toHaveBeenCalledWith('/peers/1')
      })
    })

    describe('downloadPeerConfig', () => {
      it('should call request with correct config for blob response', () => {
        const peerId = 1

        api.peerAPI.downloadPeerConfig(peerId)

        expect(request).toHaveBeenCalledWith({
          url: '/peers/1/config',
          method: 'get',
          responseType: 'blob'
        })
      })
    })

    describe('togglePeer', () => {
      it('should call request.post with correct endpoint', () => {
        const peerId = 1

        api.peerAPI.togglePeer(peerId)

        expect(request.post).toHaveBeenCalledWith('/peers/1/toggle')
      })
    })
  })

  describe('aclAPI', () => {
    describe('getACLs', () => {
      it('should call request.get with correct endpoint', () => {
        api.aclAPI.getACLs()

        expect(request.get).toHaveBeenCalledWith('/acls')
      })
    })

    describe('createACL', () => {
      it('should call request.post with correct parameters', () => {
        const aclData = { name: 'test-acl', source: '10.0.0.1' }

        api.aclAPI.createACL(aclData)

        expect(request.post).toHaveBeenCalledWith('/acls', aclData)
      })
    })

    describe('enableACL', () => {
      it('should call request.put with correct endpoint', () => {
        const aclId = 1

        api.aclAPI.enableACL(aclId)

        expect(request.put).toHaveBeenCalledWith('/acls/1/enable')
      })
    })

    describe('disableACL', () => {
      it('should call request.put with correct endpoint', () => {
        const aclId = 1

        api.aclAPI.disableACL(aclId)

        expect(request.put).toHaveBeenCalledWith('/acls/1/disable')
      })
    })
  })

  describe('batchAPI', () => {
    describe('batchCreatePeers', () => {
      it('should call request.post with correct parameters', () => {
        const peersData = [{ name: 'peer1' }, { name: 'peer2' }]

        api.batchAPI.batchCreatePeers(peersData)

        expect(request.post).toHaveBeenCalledWith('/peers/batch', peersData)
      })
    })

    describe('batchTogglePeers', () => {
      it('should call request.post with correct parameters', () => {
        const toggleData = { ids: [1, 2], enabled: true }

        api.batchAPI.batchTogglePeers(toggleData)

        expect(request.post).toHaveBeenCalledWith('/peers/batch-toggle', toggleData)
      })
    })

    describe('batchDeletePeers', () => {
      it('should call request.delete with correct parameters', () => {
        const deleteData = { ids: [1, 2] }

        api.batchAPI.batchDeletePeers(deleteData)

        expect(request.delete).toHaveBeenCalledWith('/peers/batch', { data: deleteData })
      })
    })
  })

  describe('systemAPI', () => {
    describe('health', () => {
      it('should call request.get with correct endpoint', () => {
        api.systemAPI.health()

        expect(request.get).toHaveBeenCalledWith('/health')
      })
    })
  })

  describe('backupAPI', () => {
    describe('exportConfig', () => {
      it('should call request.get with correct endpoint', () => {
        api.backupAPI.exportConfig()

        expect(request.get).toHaveBeenCalledWith('/backup/export')
      })
    })

    describe('importConfig', () => {
      it('should call request.post with correct parameters', () => {
        const configData = { config: 'test-config' }

        api.backupAPI.importConfig(configData)

        expect(request.post).toHaveBeenCalledWith('/backup/import', configData)
      })
    })
  })
})

import React, { useEffect, useState, useRef } from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import { Camera, CameraType } from 'expo-camera';
import { useIsFocused } from '@react-navigation/native';

export default function PermissionsScreen() {
  const [hasCameraPermission, setHasCameraPermission] = useState(false);
  const [hasMicrophonePermission, setHasMicrophonePermission] = useState(false);
  const [permissionChecked, setPermissionChecked] = useState(false);
  const [cameraType, setCameraType] = useState(CameraType.back);
  const [cameraTypes, setCameraTypes] = useState([]);
  const isFocused = useIsFocused();
  const cameraRef = useRef(null);

  useEffect(() => {
    async function loadPermissions() {
      const { status: cameraStatus } = await Camera.getCameraPermissionsAsync();
      const { status: micStatus } = await Camera.getMicrophonePermissionsAsync();
      setHasCameraPermission(cameraStatus === 'granted');
      setHasMicrophonePermission(micStatus === 'granted');
      setPermissionChecked(true);
    }
    loadPermissions();

    Camera.getAvailableCameraTypesAsync()
      .then((types) => setCameraTypes(types || []))
      .catch(() => setCameraTypes([]));
  }, []);

  async function requestAllPermissions() {
    try {
      const cameraPermission = await Camera.requestCameraPermissionsAsync();
      const micPermission = await Camera.requestMicrophonePermissionsAsync();

      const cameraGranted = cameraPermission.status === 'granted';
      const micGranted = micPermission.status === 'granted';

      setHasCameraPermission(cameraGranted);
      setHasMicrophonePermission(micGranted);
      setPermissionChecked(true);

      if (!cameraGranted || !micGranted) {
        alert('Camera and microphone access are required for attendance verification.');
      }
    } catch (error) {
      console.error('Permission request failed:', error);
      setPermissionChecked(true);
    }
  }

  function toggleCameraType() {
    setCameraType((current) =>
      current === CameraType.back ? CameraType.front : CameraType.back
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Camera and Microphone</Text>
      <Text style={styles.subtitle}>Request device access and preview the camera.</Text>

      <View style={styles.statusBox}>
        <Text style={styles.statusText}>Camera permission: {hasCameraPermission ? 'Granted' : 'Denied'}</Text>
        <Text style={styles.statusText}>Microphone permission: {hasMicrophonePermission ? 'Granted' : 'Denied'}</Text>
        <Text style={styles.statusText}>Available camera types: {cameraTypes.join(', ') || 'Unknown'}</Text>
      </View>

      <Button title="Request Camera + Microphone" onPress={requestAllPermissions} />
      <View style={styles.spacer} />
      <Button title="Switch Camera" onPress={toggleCameraType} disabled={!hasCameraPermission} />

      {permissionChecked && hasCameraPermission && isFocused ? (
        <View style={styles.previewContainer}>
          <Camera
            ref={cameraRef}
            style={styles.preview}
            type={cameraType}
            ratio="16:9"
          />
        </View>
      ) : (
        <View style={styles.previewPlaceholder}>
          <Text style={styles.previewText}>Camera preview is unavailable until permissions are granted.</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#555',
    marginBottom: 16,
  },
  statusBox: {
    marginBottom: 16,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    backgroundColor: '#f9f9f9',
  },
  statusText: {
    fontSize: 14,
    marginBottom: 4,
  },
  spacer: {
    height: 12,
  },
  previewContainer: {
    flex: 1,
    marginTop: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  preview: {
    flex: 1,
    width: '100%',
  },
  previewPlaceholder: {
    flex: 1,
    marginTop: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#ddd',
    backgroundColor: '#f1f1f1',
  },
  previewText: {
    color: '#555',
    textAlign: 'center',
    paddingHorizontal: 16,
  },
});
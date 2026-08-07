import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';

export default function AttendanceScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Attendance</Text>
      <Text style={styles.subtitle}>This screen can be extended for face and voice attendance.</Text>
      <Button title="Camera & Microphone" onPress={() => navigation.navigate('Permissions')} />
      <View style={styles.spacer} />
      <Button title="Back to Dashboard" onPress={() => navigation.goBack()} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    marginBottom: 24,
    color: '#555',
    textAlign: 'center',
  },
  spacer: {
    height: 16,
  },
});
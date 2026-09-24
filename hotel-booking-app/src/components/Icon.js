import React from 'react';
import {MaterialCommunityIcons} from '@expo/vector-icons';

const Icon = ({name, color = '#27899A', size = 36}) => (
  <MaterialCommunityIcons name={name} color={color} size={size} />
);

export default Icon;

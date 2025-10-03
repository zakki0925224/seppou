import { Box, VStack, Text } from "@chakra-ui/react";

export function Recommends() {
    return (
        <Box w="300px" h="100vh" p={4}>
            <VStack alignItems="start" gap={4}>
                <Box w="full" p={4} bg="gray.100" borderRadius="md">
                    <Text fontSize="lg" fontWeight="bold" mb={2}>おすすめトレンド</Text>
                    <VStack alignItems="start" gap={2}>
                        <Text fontSize="sm" color="gray.600">#プログラミング</Text>
                        <Text fontSize="sm" color="gray.600">#React</Text>
                        <Text fontSize="sm" color="gray.600">#JavaScript</Text>
                    </VStack>
                </Box>
                <Box w="full" p={4} bg="gray.100" borderRadius="md">
                    <Text fontSize="lg" fontWeight="bold" mb={2}>おすすめユーザー</Text>
                    <VStack alignItems="start" gap={2}>
                        <Text fontSize="sm">@developer1</Text>
                        <Text fontSize="sm">@designer2</Text>
                        <Text fontSize="sm">@engineer3</Text>
                    </VStack>
                </Box>
            </VStack>
        </Box>
    )
}

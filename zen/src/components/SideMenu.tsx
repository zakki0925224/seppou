import { Box, VStack, Text, HStack } from "@chakra-ui/react";
import { LuHouse, LuSearch, LuBell, LuMail, LuUser } from "react-icons/lu";

export function SideMenu() {
    return (
        <Box w="250px" h="100vh" p={4} borderRight="1px" borderColor="gray.200">
            <VStack alignItems="start" gap={4}>
                <Text fontSize="xl" fontWeight="bold">メニュー</Text>
                <HStack cursor="pointer" _hover={{ bg: "gray.100" }} p={2} borderRadius="md" w="full">
                    <LuHouse size={20} />
                    <Text>ホーム</Text>
                </HStack>
                <HStack cursor="pointer" _hover={{ bg: "gray.100" }} p={2} borderRadius="md" w="full">
                    <LuSearch size={20} />
                    <Text>探索</Text>
                </HStack>
                <HStack cursor="pointer" _hover={{ bg: "gray.100" }} p={2} borderRadius="md" w="full">
                    <LuBell size={20} />
                    <Text>通知</Text>
                </HStack>
                <HStack cursor="pointer" _hover={{ bg: "gray.100" }} p={2} borderRadius="md" w="full">
                    <LuMail size={20} />
                    <Text>メッセージ</Text>
                </HStack>
                <HStack cursor="pointer" _hover={{ bg: "gray.100" }} p={2} borderRadius="md" w="full">
                    <LuUser size={20} />
                    <Text>プロフィール</Text>
                </HStack>
            </VStack>
        </Box>
    )
}

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Login, GetErrorMessage } from "@/api/login";

const loginSchema = z.object({
    username: z.string().email("유효한 이메일 형식이 아닙니다."),
    password: z.string().min(1, "비밀번호를 입력해주세요."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

interface UseLoginProps {
    onLogin?: () => void;
}

export const useLogin = ({ onLogin }:
     UseLoginProps = {}) => {
        const navigate = useNavigate();
        const [isLoading, setIsLoading] = useState(false);
        const [apiError, setApiError] = useState<string | null>(null);

        const form =
        useForm<LoginFormValues>({
            resolver: zodResolver(loginSchema),
            defaultValues: {
                username: "",
                password: "",
            },
        });

        const {
            register,
            handleSubmit,
            formState: { errors },
        } = form;

        const onSubmit = async (data: LoginFormValues) => {
            setIsLoading(true);
            setApiError(null);

            try {
                const result = await Login({
                    username: data.username,
                    password: data.password,
                });

                if (result.status === "SUCCESS") {
                    // 토큰을 로컬 스토리지에 저장
                    console.log('🔐 로그인 성공 - 토큰 저장 중...');
                    console.log('Access Token:', result.data.token.access_token);
                    console.log('Refresh Token:', result.data.token.refresh_token);
                    
                    localStorage.setItem('access_token', result.data.token.access_token);
                    localStorage.setItem('refresh_token', result.data.token.refresh_token);
                    
                    // 저장 확인
                    const savedToken = localStorage.getItem('access_token');
                    console.log('✅ 토큰 저장 확인:', savedToken ? '성공' : '실패');
                    
                    toast.success("로그인이 완료되었습니다!");
                    onLogin?.();
                    navigate("/");
                } else {
                    const errorMessage =
                    GetErrorMessage(result.error?.code, result.error?.message) ||
                    "로그인에 실패했습니다.";
                    setApiError(errorMessage);
                }
            } catch {
                setApiError("네트워크 오류가 발생했습니다. 다시 시도해주세요.");
            } finally {
                setIsLoading(false);
            }
        };

        const handleToggleMode = () => {
            navigate("/signup");
        };

        return {
            form,
            register,
            handleSubmit,
            errors,
            isLoading,
            apiError,
            onSubmit,
            handleToggleMode,
        };
    };

    export default useLogin;